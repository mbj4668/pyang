<?xml version="1.0" encoding="utf-8"?>

<!-- This stylesheet composes base file name for output DSDL schemas. -->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
                version="1.0">
  <xsl:output method="text" encoding="utf-8"/>

  <xsl:variable name="NL">
    <xsl:text>
</xsl:text>
  </xsl:variable>

  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="not(//svrl:failed-assert|//svrl:successful-report)">
        <xsl:text>No errors found.</xsl:text>
        <xsl:value-of select="$NL"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates
            select="//svrl:failed-assert|//svrl:successful-report"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="svrl:failed-assert">
    <xsl:text>Failed assert at </xsl:text>
    <xsl:value-of
        select="preceding-sibling::svrl:fired-rule[1]/@context"/>
    <xsl:value-of select="concat(':',$NL)"/>
    <xsl:value-of select="concat(svrl:text,$NL)"/>
  </xsl:template>

  <xsl:template match="svrl:successful-report">
    <xsl:text>Validity error at </xsl:text>
    <xsl:value-of
        select="preceding-sibling::svrl:fired-rule[1]/@context"/>
    <xsl:value-of select="concat(':',$NL)"/>
    <xsl:value-of select="concat(svrl:text,$NL)"/>
  </xsl:template>

</xsl:stylesheet>
