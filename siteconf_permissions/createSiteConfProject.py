#!/usr/bin/python3
import gitlab
from gitlab.exceptions import GitlabCreateError
from gitlab.exceptions import GitlabHttpError

import sys
import logging
import argparse


def get_project(name, force, gl):
    logging.info("Retrieving SITECONF group id")
    siteconf_id = gl.groups.get("SITECONF").id
    try:
        logging.info("Creating SITECONF project for {}".format(name))
        #return gl.projects.create({"name": "TEST", "namespace_id": siteconf_id})
        return gl.projects.create({"name": name, "namespace_id": siteconf_id})
    except (GitlabCreateError, GitlabHttpError) as e:
        if e.error_message['name'][0] == "has already been taken":
            if force:
                logging.info("SITECONF project already exists, retrieving SITECONF project")
                return gl.projects.get("SITECONF/{}".format(name))
            else:
                logging.error("SITECONF project already exists, use the -f flag to retrieve the site instead")
                raise e
        else:
            raise e


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="create a new SITECONF project")
    parser.add_argument("-f", "--force", dest="force", action="store_true", help="Overwrite the existing SITECONF project")
    parser.add_argument("-V", "--verbose", dest="verbose", action="store_true", help="show the full logs")
    parser.add_argument("name", metavar="name", type=str, nargs=1, help="name of the site")

    args = parser.parse_args()

    name = args.name[0]
    force = args.force
    level = logging.INFO if args.verbose else logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    gl_url = "https://gitlab.cern.ch"
    logging.info("Looking for gitlab token file")
    with open("./gitlabToken", "r") as f:
    	gl_token = f.read().strip()

    logging.info("Connecting to gitlab")
    gl = gitlab.Gitlab(gl_url, private_token=gl_token)

    project = get_project(name, force, gl)

    logging.info("Setting description, visibility and path")
    project.description = "{} site configuration".format(name)
    project.visiblity = "private"
    project.path = name

    logging.info("Adding empty file to repository")
    try:
        project.files.create({"file_path": "JobConfig/site-local-config.xml", "content": "", "branch": "master", "commit_message": "First Commit"})
    except (GitlabCreateError, GitlabHttpError) as e:
        if e.error_message == "A file with this name already exists":
            logging.warning("JobConfig/site-local-config.xml already exists")
        else:
            raise e

    logging.info("Changing access levels to master")
    try:
        project.protectedbranches.delete("master")
    except:
        # If branch does not exists, we still create it
        pass
    project.protectedbranches.create({
        "name": "master",
        "allowed_to_push": [{"access_level": gitlab.DEVELOPER_ACCESS}],
        "allowed_to_merge": [{"access_level": gitlab.DEVELOPER_ACCESS}],
        "allowed_to_unprotect": [{"access_level": gitlab.MAINTAINER_ACCESS}]
    })

    logging.info("Enabling emails on push service")
    service = project.services.get("emails-on-push")
    service.active = True
    service.recipients = "cms-comp-ops-site-support-team@cern.ch"
    service.save()

    logging.info("Retrieving cmssst user id")
    cmssst = gl.users.list(search="cmssst")[0].id
    logging.info("Adding the cmssst user as maintainer")
    try:
        project.members.create({"user_id": cmssst, "access_level": gitlab.MAINTAINER_ACCESS})
    except (GitlabCreateError, GitlabHttpError) as e:
        if e.error_message['access_level'][0] == "should be greater than or equal to Owner inherited membership from group siteconf":
            pass
        elif e.error_message == "Member already exists":
            logging.info("The cmssst user is already a member, changing access level anyway")
            user = project.members.get(cmssst)
            user.access_level = gitlab.MAINTAINER_ACCESS
            user.save()
        else:
            raise e

    project.save()
    logging.info("SITECONF project for {} was created succesfully".format(name))
