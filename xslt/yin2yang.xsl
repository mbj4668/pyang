<?xml version="1.0"?>

<!-- Program name: yin2yang.xsl

Copyright © 2011 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Translates YIN XML syntax to YANG compact syntax (see RFC 6110).

NOTES:

1. XML comments outside arguments are translated to YANG comments. 

2. The stylesheet doesn't attempt to reformat or otherwise transform
   text arguments, so occassionally the result may not be valid YANG.

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
		xmlns:yin="urn:ietf:params:xml:ns:yang:yin:1"
		version="1.0">
  <xsl:output method="text"/>
  <xsl:strip-space elements="*"/>

  <xsl:template name="indent">
    <xsl:param name="level" select="0"/>
    <xsl:if test="$level>0">
      <xsl:text>  </xsl:text>
      <xsl:call-template name="indent">
	<xsl:with-param name="level" select="$level - 1"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <xsl:template name="semi-or-sub">
    <xsl:choose>
      <xsl:when test="*">
	<xsl:text> {&#xA;</xsl:text>
	<xsl:apply-templates select="*|comment()"/>
	<xsl:call-template name="indent">
	  <xsl:with-param name="level"
			  select="count(ancestor::*)"/>
	</xsl:call-template>
	<xsl:text>}&#xA;</xsl:text>
      </xsl:when>
      <xsl:otherwise>
	<xsl:text>;&#xA;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="keyword">
    <xsl:if test="count(ancestor::yin:*)=1">
      <xsl:text>&#xA;</xsl:text>
    </xsl:if>
    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="count(ancestor::*)"/>
    </xsl:call-template>
    <xsl:value-of select="local-name(.)"/>
  </xsl:template>

  <xsl:template name="statement">
    <xsl:param name="quote"/>
    <xsl:param name="arg"/>
    <xsl:call-template name="keyword"/>
    <xsl:value-of select="concat(' ',$quote,$arg,$quote)"/>
    <xsl:call-template name="semi-or-sub"/>
  </xsl:template>

  <!-- Root element -->

  <xsl:template match="/">
    <xsl:apply-templates select="yin:module|yin:submodule|comment()"/>
  </xsl:template>

  <xsl:template
      match="yin:anyxml|yin:argument|yin:base|yin:bit|yin:case
	     |yin:choice|yin:container|yin:enum|yin:extension
	     |yin:feature|yin:grouping|yin:identity|yin:if-feature
	     |yin:leaf|yin:leaf-list|yin:list|yin:module
	     |yin:notification|yin:rpc|yin:submodule|yin:type
	     |yin:typedef|yin:uses">
    <xsl:call-template name="statement">
      <xsl:with-param name="arg" select="@name"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:units">
    <xsl:call-template name="statement">
      <xsl:with-param name="quote">"</xsl:with-param>
      <xsl:with-param name="arg" select="@name"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:augment|yin:deviation|yin:refine">
    <xsl:call-template name="statement">
      <xsl:with-param name="quote">"</xsl:with-param>
      <xsl:with-param name="arg" select="@target-node"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:belongs-to|yin:import|yin:include">
    <xsl:call-template name="statement">
      <xsl:with-param name="arg" select="@module"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template
      match="yin:config|yin:default|yin:deviate|yin:error-app-tag
	     |yin:fraction-digits|yin:key|yin:length|yin:mandatory
	     |yin:max-elements|yin:min-elements|yin:ordered-by
	     |yin:path|yin:pattern|yin:position|yin:prefix
	     |yin:presence|yin:range|yin:require-instance
	     |yin:status|yin:value|yin:yang-version|yin:yin-element">
    <xsl:call-template name="statement">
      <xsl:with-param name="quote">"</xsl:with-param>
      <xsl:with-param name="arg" select="@value"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:error-message">
    <xsl:call-template name="keyword"/>
    <xsl:apply-templates select="yin:value"/>
  </xsl:template>

  <xsl:template match="yin:contact|yin:description
		       |yin:organization|yin:reference">
    <xsl:call-template name="keyword"/>
    <xsl:apply-templates select="yin:text"/>
  </xsl:template>

  <xsl:template match="yin:input|yin:output">
    <xsl:call-template name="keyword"/>
    <xsl:call-template name="semi-or-sub"/>
  </xsl:template>

  <xsl:template match="yin:must|yin:when">
    <xsl:call-template name="statement">
      <xsl:with-param name="quote">"</xsl:with-param>
      <xsl:with-param name="arg" select="@condition"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:namespace">
    <xsl:call-template name="statement">
      <xsl:with-param name="quote">"</xsl:with-param>
      <xsl:with-param name="arg" select="@uri"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:revision|yin:revision-date">
    <xsl:call-template name="statement">
      <xsl:with-param name="arg" select="@date"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:unique">
    <xsl:call-template name="statement">
      <xsl:with-param name="quote">"</xsl:with-param>
      <xsl:with-param name="arg" select="@tag"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="yin:text|yin:value">
    <xsl:variable name="qchar">
      <xsl:choose>
	<xsl:when test="contains(.,'&quot;')">
	  <xsl:text>'</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:text>"</xsl:text>
	</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:text>&#xA;</xsl:text>
    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="count(ancestor::*) - 1"/>
    </xsl:call-template>
    <xsl:value-of select="concat(' ',$qchar)"/>
    <xsl:apply-templates select="text()"/>
    <xsl:value-of select="$qchar"/>
    <xsl:call-template name="semi-or-sub"/>
  </xsl:template>

  <xsl:template match="comment()">
    <xsl:if test="count(ancestor::yin:*)=1">
      <xsl:text>&#xA;</xsl:text>
    </xsl:if>
    <xsl:call-template name="indent">
      <xsl:with-param name="level" select="count(ancestor::*)"/>
    </xsl:call-template>
    <xsl:text>/*</xsl:text>
    <xsl:value-of select="."/>
    <xsl:text>*/&#xA;</xsl:text>
  </xsl:template>

</xsl:stylesheet>
