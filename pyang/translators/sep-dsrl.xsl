<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: sep-dsrl.xsl

Copyright © 2007 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Picks DSRL defaults from DSDL data model and makes them stand-alone.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:rng="http://relaxng.org/ns/structure/1.0"
		xmlns:dsrl="http://purl.oclc.org/dsdl/dsrl"
                version="1.0">

  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="rng:element|rng:ref" mode="path">
    <xsl:apply-templates select="ancestor::rng:define" mode="path"/>
    <xsl:for-each select="ancestor::rng:element">
      <xsl:text>/</xsl:text>
      <xsl:value-of select="@name"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="rng:define" mode="path">
    <xsl:variable name="name" select="@name"/>
    <xsl:variable name="refs" select="//rng:ref[@name=$name]"/>
    <xsl:choose>
      <xsl:when test="not($refs)">
	<xsl:value-of select="$name"/>
      </xsl:when>
      <xsl:when test="count($refs)=1">
	<xsl:apply-templates select="$refs" mode="path"/>
      </xsl:when>
      <xsl:otherwise>
	<xsl:text>(</xsl:text>
	<xsl:for-each select="$refs">
	  <xsl:apply-templates select="." mode="path"/>
	  <xsl:if test="position()!=last()">
	    <xsl:text>|</xsl:text>
	  </xsl:if>
	</xsl:for-each>
	<xsl:text>)</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
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
	<xsl:apply-templates select=".." mode="path"/>
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
