<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: sep-schematron.xsl

Copyright © 2008 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Picks Schematron rules from DSDL data model and makes them stand-alone.

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
		xmlns:sch="http://purl.oclc.org/dsdl/schematron"
                version="1.0">

  <xsl:output method="xml" indent="yes"/>

  <xsl:param name="model-prefix">nm</xsl:param>

  <xsl:template name="elem-path">
    <xsl:for-each select="ancestor::rng:element">
      <xsl:value-of select="concat('/', $model-prefix)"/>
      <xsl:value-of select="concat(':', @name)"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="/">
    <xsl:element name="sch:schema">
      <xsl:element name="sch:ns">
	<xsl:attribute name="uri">
	  <xsl:value-of select="rng:grammar/@ns"/>
	</xsl:attribute>
	<xsl:attribute name="prefix">
	  <xsl:value-of select="$model-prefix"/>
	</xsl:attribute>
      </xsl:element>
      <xsl:apply-templates select="//sch:assert"/>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="sch:assert">
    <xsl:variable name="def" select="ancestor::rng:define"/>
    <xsl:choose>
      <xsl:when test="$def">
	<xsl:element name="sch:pattern">
	  <xsl:attribute name="abstract">true</xsl:attribute>
	  <xsl:attribute name="id">
	    <xsl:value-of select="$def/@name"/>
	  </xsl:attribute>
	  <xsl:element name="sch:rule">
	    <xsl:attribute name="context">
	      <xsl:text>$head</xsl:text>
	      <xsl:call-template name="elem-path"/>
	    </xsl:attribute>
	    <xsl:copy>
	      <xsl:apply-templates select="*|@test|text()"/>
	    </xsl:copy>
	  </xsl:element>
	</xsl:element>
      </xsl:when>
      <xsl:otherwise>
	<xsl:element name="sch:pattern">
	  <xsl:element name="sch:rule">
	    <xsl:attribute name="context">
	      <xsl:call-template name="elem-path"/>
	    </xsl:attribute>
	    <xsl:copy>
	      <xsl:apply-templates select="sch:*|@test|text()"/>
	    </xsl:copy>
	  </xsl:element>
	</xsl:element>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="@test">
    <xsl:copy>
      <xsl:value-of select="."/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="sch:*">
    <xsl:copy/>
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

</xsl:stylesheet>
