#! /usr/bin/python3
import gitlab
import requests
import json
import re
import logging
from gitlab.exceptions import GitlabGetError


def raise_exception(msg):
    logging.error(msg)
    raise Exception(msg)


def get_facilities(url, cert, key):
    facility_regex = re.compile(r"[A-Z]{2,2}_\w+")

    logging.info("Requesting facilities from CRIC")
    result = requests.get(url, cert=(cert, key), verify=False)

    if result.status_code == 200:
        logging.info("CRIC request was successful")
        doc = json.loads(result.text)
        facilities = {}

        for site in doc.keys():
            facility = doc[site]["facility"].split()[0]
            if facility_regex.match(facility):
                facilities[site] = facility

        if len(facilities) == 0:
            raise_exception("Facilities list from CRIC is empty")

        return facilities
    else:
        raise_exception("CRIC request failed with status code {}".format(result.status_code))


def create_group(name, gl):
    logging.info("Looking for {} group".format(name))
    try:
        group = gl.groups.get(name)
        logging.info("{} group already exists".format(name))
    except GitlabGetError:
        logging.info("{} group does not exists, creating it".format(name))
        group = gl.groups.create({"name": name, "path": name})
        group.add_ldap_group_link(name, gitlab.DEVELOPER_ACCESS, "ldapmain")
        group.ldap_sync()
        group.save()
    return group


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    cric_url = "https://cms-cric.cern.ch/api/cms/site/query/?json"

    user_cert = "/tmp/x509up_u79522"
    user_key = "/tmp/x509up_u79522"

    gl_url = "https://gitlab.cern.ch"

    logging.info("Looking for gitlab token file")
    with open("./gitlabToken", "r") as f:
    	gl_token = f.read().strip() 

    logging.info("Connecting to {}".format(gl_url))
    gl = gitlab.Gitlab(gl_url, private_token=gl_token)

    logging.info("Getting SITECONF projects")
    siteconf = gl.groups.get("SITECONF")
    # Get all the projects inside the SITECONF group
    projects = siteconf.projects.list(all=True)
    # Get all the site's facilities from CRIC
    facilities = get_facilities(cric_url, user_cert, user_key)

    groups_regex = re.compile(r"cms\-[A-Z]{2,2}_\w+\-(exec|admin)")

    for project in projects:
        project = gl.projects.get(project.id)

        site = project.attributes["name"]
        groups = project.attributes["shared_with_groups"]

        if site in facilities:
            facility = facilities[site]
            group_names = ["cms-" + facility + "-admin", "cms-" + facility + "-exec"]
            for group_name in group_names:
                if not any(group["group_name"] == group_name for group in groups):
                    group = create_group(group_name, gl)
                    logging.info("Sharing the {} SITECONF project with {}".format(site, group_name))
                    project.share(group.get_id(), gitlab.DEVELOPER_ACCESS)
                else:
                    logging.info("The {} SITECONF project was already shared with {}".format(site, group_name))
            project.save()
        else:
            logging.warning("The {} SITECONF project does not have a CRIC entry".format(site))
