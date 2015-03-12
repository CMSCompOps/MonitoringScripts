<?xml version="1.0" encoding="gb2312"?><!-- DWXMLSource="space.xml" --><!DOCTYPE xsl:stylesheet  [
	<!ENTITY nbsp   "&#160;">
	<!ENTITY copy   "&#169;">
	<!ENTITY reg    "&#174;">
	<!ENTITY trade  "&#8482;">
	<!ENTITY mdash  "&#8212;">
	<!ENTITY ldquo  "&#8220;">
	<!ENTITY rdquo  "&#8221;"> 
	<!ENTITY pound  "&#163;">
	<!ENTITY yen    "&#165;">
	<!ENTITY euro   "&#8364;">
]>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="gb2312" doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"/>
<xsl:template match="/">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=gb2312"/>
<title>SITE SPACE MONITOR</title>
<style type="text/css">
<xsl:comment>
.STYLE1 {
	font-family: Arial, Helvetica, sans-serif;
	font-weight: bold;
}
.STYLE2 {font-family: Arial, Helvetica, sans-serif}
</xsl:comment>
</style>
</head>

<body>

<p align="center" class="STYLE1"><font color="#0099FF" size="+6" face="Geneva, Arial, Helvetica, sans-serif">SITE SPACE MONITORING</font></p>
<p align="center" class="STYLE1 STYLE2"><font color="#0099FF" size="6" face="Geneva, Arial, Helvetica, sans-serif">T0 Center</font></p>
<table width="1268" border="1">
    <tr>
      <th width="234" height="35" scope="col">site</th>
        <th width="268" scope="col">pledge</th>
        <th width="244" scope="col">suscriptions</th>
        <th width="244" scope="col">on-site</th>
        <th width="244" scope="col">used</th>
    </tr> 
	<xsl:for-each select="html/body/sitelist/T0/site">
      <tr>
        <th height="35" scope="col"><xsl:value-of select="name"/></th>
        <th scope="col"><xsl:value-of select="pledge"/></th>
        <th scope="col"><xsl:value-of select="subscriptions"/></th>
        <th scope="col"><xsl:value-of select="on-site"/></th>
        <th scope="col"><xsl:value-of select="used"/></th>
       </tr>
	</xsl:for-each>  
  </table>
<div align="center"><font color="#0099FF" size="6" face="Geneva, Arial, Helvetica, sans-serif">T1 Center</font></div>
<table width="1268" border="1">
  <tr>
    <th width="234" height="35" scope="col">site</th>
    <th width="268" scope="col">pledge</th>
    <th width="244" scope="col">suscriptions</th>
    <th width="244" scope="col">on-site</th>
    <th width="244" scope="col">used</th>
  </tr>
    <xsl:for-each select="html/body/sitelist/T1/site">
      <tr>
        <th height="35" scope="col"><xsl:value-of select="name"/></th>
        <th scope="col"><xsl:value-of select="pledge"/></th>
        <th scope="col"><xsl:value-of select="subscriptions"/></th>
        <th scope="col"><xsl:value-of select="on-site"/></th>
        <th scope="col"><xsl:value-of select="used"/></th>
      </tr>
    </xsl:for-each>
 </table>
<div align="center"><font color="#0099FF" size="6" face="Geneva, Arial, Helvetica, sans-serif">T2 Center</font></div>
<table width="1268" border="1">
  <tr>
    <th width="234" height="35" scope="col">site</th>
    <th width="268" scope="col">pledge</th>
    <th width="244" scope="col">suscriptions</th>
    <th width="244" scope="col">on-site</th>
    <th width="244" scope="col">used</th>
  </tr>
    <xsl:for-each select="html/body/sitelist/T2/site">
      <tr>
        <th height="35" scope="col"><xsl:value-of select="name"/></th>
        <th scope="col"><xsl:value-of select="pledge"/></th>
        <th scope="col"><xsl:value-of select="subscriptions"/></th>
        <th scope="col"><xsl:value-of select="on-site"/></th>
        <th scope="col"><xsl:value-of select="used"/></th>
      </tr>
    </xsl:for-each>
</table>
<div align="center"><font color="#0099FF" size="6" face="Geneva, Arial, Helvetica, sans-serif">T3 Center</font></div>
<table width="1268" border="1">
  <tr>
    <th width="234" height="35" scope="col">site</th>
    <th width="268" scope="col">pledge</th>
    <th width="244" scope="col">suscriptions</th>
    <th width="244" scope="col">on-site</th>
    <th width="244" scope="col">used</th>
  </tr>
    <xsl:for-each select="html/body/sitelist/T3/site">
      <tr>
        <th height="35" scope="col"><xsl:value-of select="name"/></th>
        <th scope="col"><xsl:value-of select="pledge"/></th>
        <th scope="col"><xsl:value-of select="subscriptions"/></th>
        <th scope="col"><xsl:value-of select="on-site"/></th>
        <th scope="col"><xsl:value-of select="used"/></th>
      </tr>
    </xsl:for-each>
</table>
</body>
</html>

</xsl:template>
</xsl:stylesheet>
