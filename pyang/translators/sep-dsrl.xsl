<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: sep-dsrl.xsl

Copyright © 2007 Ladislav Lhotka, CESNET

Picks DSRL defaults from DSDL data model and makes them stand-alone.
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:rng="http://relaxng.org/ns/structure/1.0"
		xmlns:dsrl="http://purl.oclc.org/dsdl/dsrl"
                version="1.0">

  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="rng:element" mode="path">

  </xsl:template>

  <xsl:template match="rng:define" mode="path">

  </xsl:template>

  <xsl:template match="rng:ref" mode="path">

  </xsl:template>

  <xsl:template match="/">
    <xsl:element name="dsrl:maps">
      <xsl:attribute name="targetNamespace">
	<xsl:value-of select="rng:grammar/@ns"/>
      </xsl:attribute>
      <xsl:apply-templates select="//dsrl:default-content"/>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="dsrl:default-content">
    <xsl:element name="dsrl:element-map">
      <xsl:element name="dsrl:within">
	<xsl:call-template name="full-path"/>
      </xsl:element>
      <xsl:element name="dsrl:name">
	<xsl:value-of select="../@name"/>
      </xsl:element>
      <xsl:copy>
	<xsl:value-of select="."/>
      </xsl:copy>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
