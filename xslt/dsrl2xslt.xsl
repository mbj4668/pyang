<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: dsrl2xslt.xsl

Copyright © 2010 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Translates subset of DSRL to an XSLT stylesheet.

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

<!-- NOTE: This stylesheet translates only a subset of DSRL which is
     used in NETMOD, i.e. specification of default content. -->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:dsrl="http://purl.oclc.org/dsdl/dsrl"
                version="1.0">

  <xsl:output method="xml"/>

  <xsl:template match="dsrl:maps">
    <xsl:element name="xsl:stylesheet">
      <xsl:copy-of select="namespace::*"/>
      <xsl:attribute name="version">1.0</xsl:attribute>
      <xsl:element name="xsl:output">
        <xsl:attribute name="method">xml</xsl:attribute>
        <xsl:attribute name="encoding">utf-8</xsl:attribute>
      </xsl:element>
      <xsl:element name="xsl:strip-space">
        <xsl:attribute name="elements">*</xsl:attribute>
      </xsl:element>
      <xsl:apply-templates
          select="dsrl:element-map[not(dsrl:parent =
                  preceding-sibling::dsrl:element-map/dsrl-parent)]"/>
      <xsl:element name="xsl:template">
        <xsl:attribute name="match">*|@*</xsl:attribute>
        <xsl:element name="xsl:copy">
          <xsl:element name="xsl:apply-templates">
            <xsl:attribute name="select">*|@*|text()</xsl:attribute>
          </xsl:element>
        </xsl:element>
      </xsl:element>
    </xsl:element>
  </xsl:template>

  <xsl:template match="dsrl:element-map">
    <xsl:variable name="parent" select="normalize-space(dsrl:parent)"/>
    <xsl:element name="xsl:template">
      <xsl:attribute name="match">
        <xsl:value-of select="$parent"/>
      </xsl:attribute>
      <xsl:element name="xsl:copy">
        <xsl:element name="xsl:apply-templates">
          <xsl:attribute name="select">*|@*|text()</xsl:attribute>
        </xsl:element>
        <xsl:for-each select="../dsrl:element-map
                              [normalize-space(dsrl:parent)=$parent]">
          <xsl:variable name="name" select="dsrl:name"/>
          <xsl:element name="xsl:if">
            <xsl:attribute name="test">
              <xsl:value-of select="concat('not(', $name, ')')"/>
            </xsl:attribute>
            <xsl:variable name="ns"
                          select="/dsrl:maps/namespace::*[name() =
                                  substring-before($name,':')]"/>
            <xsl:element name="{$name}" namespace="{$ns}">
	      <xsl:element name="xsl:processing-instruction">
		<xsl:attribute name="name">dsrl</xsl:attribute>
	      </xsl:element>
              <xsl:copy-of select="dsrl:default-content/*
                                   |dsrl:default-content/text()"/>
            </xsl:element>
          </xsl:element>
        </xsl:for-each>
      </xsl:element>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
