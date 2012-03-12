<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: gen-dsrl.xsl

Copyright © 2011 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Creates DSRL schema from the hybrid DSDL schema (RFC 6110).

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
                xmlns:exsl="http://exslt.org/common"
                extension-element-prefixes="exsl"
                xmlns:rng="http://relaxng.org/ns/structure/1.0"
                xmlns:dsrl="http://purl.oclc.org/dsdl/dsrl"
                xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
                xmlns:en="urn:ietf:params:xml:ns:netconf:notification:1.0"
                xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                version="1.0">

  <xsl:output method="xml" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>

  <xsl:include href="gen-common.xsl"/>

  <xsl:template name="nc-namespace">
      <xsl:choose>
        <xsl:when test="$target='config' or $target='get-reply' or
                        $target='get-config-reply' or $target='data'
                        or $target='rpc' or $target='rpc-reply'">
          <xsl:variable name="dummy">
            <nc:dummy/>
          </xsl:variable>
          <xsl:copy-of select="exsl:node-set($dummy)/*/namespace::*"/>
        </xsl:when>
        <xsl:when test="$target='notification'">
          <xsl:variable name="dummy">
            <en:dummy/>
          </xsl:variable>
          <xsl:copy-of select="exsl:node-set($dummy)/namespace::*"/>
        </xsl:when>
      </xsl:choose>
  </xsl:template>

  <xsl:template name="qname">
    <xsl:param name="prefix"/>
    <xsl:param name="name"/>
    <xsl:if test="not(contains($name,':'))">
      <xsl:value-of select="concat($prefix,':')"/>
    </xsl:if>
    <xsl:value-of select="$name"/>
  </xsl:template>

  <xsl:template name="parent-path">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:value-of select="$prevpath"/>
    <xsl:for-each select="ancestor::rng:element">
      <xsl:text>/</xsl:text>
      <xsl:call-template name="qname">
        <xsl:with-param name="prefix" select="$prefix"/>
        <xsl:with-param name="name" select="@name"/>
      </xsl:call-template>
      <xsl:if test="@nma:when">
	<xsl:value-of select="concat('[',@nma:when,']')"/>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="yam-namespaces">
    <xsl:for-each
        select="namespace::*[not(name()='xml' or .=$rng-uri or
                .=$dtdc-uri or .=$dc-uri or .=$nma-uri)]">
      <xsl:copy/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="element-map">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:param name="content"/>
    <xsl:param name="case" select="boolean(0)"/>
    <xsl:element name="dsrl:element-map">
      <xsl:element name="dsrl:parent">
        <xsl:variable name="ppath">
          <xsl:call-template name="parent-path">
            <xsl:with-param name="prevpath" select="$prevpath"/>
            <xsl:with-param name="prefix" select="$prefix"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:choose>
          <xsl:when test="$ppath=''">/</xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$ppath"/>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:if test="$case">
          <xsl:apply-templates select="ancestor::rng:choice[1]"
                               mode="cases"/>
        </xsl:if>
      </xsl:element>
      <xsl:element name="dsrl:name">
        <xsl:if test="not(contains(@name,':'))">
          <xsl:value-of select="concat($prefix,':')"/>
        </xsl:if>
        <xsl:value-of select="@name"/>
      </xsl:element>
      <xsl:element name="dsrl:default-content">
        <xsl:apply-templates select="$content" mode="copy">
          <xsl:with-param name="prefix" select="$prefix"/>
        </xsl:apply-templates>
      </xsl:element>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:choice" mode="cases">
    <xsl:text>[not(</xsl:text>
    <xsl:for-each select="rng:*[not(@nma:default or @nma:implicit='true')]">
      <xsl:apply-templates select="." mode="cases"/>
      <xsl:if test="position()!=last()">
        <xsl:text>|</xsl:text>
      </xsl:if>
    </xsl:for-each>
    <xsl:text>)]</xsl:text>
  </xsl:template>

  <xsl:template match="rng:element" mode="cases">
    <xsl:value-of select="@name"/>
  </xsl:template>

  <xsl:template match="rng:oneOrMore|rng:zeroOrMore" mode="cases">
    <xsl:apply-templates mode="cases"/>
  </xsl:template>

  <xsl:template match="rng:group|rng:interleave" mode="cases">
    <xsl:for-each select="rng:*">
      <xsl:apply-templates select="." mode="cases"/>
      <xsl:if test="position()!=last()">
        <xsl:text>|</xsl:text>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="/">
    <xsl:call-template name="check-input-pars"/>
    <xsl:element name="dsrl:maps">
      <xsl:apply-templates select="rng:grammar"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="/rng:grammar">
    <xsl:call-template name="yam-namespaces"/>
    <xsl:call-template name="nc-namespace"/>
    <xsl:apply-templates select="descendant::rng:grammar"/>
  </xsl:template>

  <xsl:template match="rng:grammar">
    <xsl:variable name="prefix"
                  select="name(namespace::*[.=current()/@ns])"/>
    <xsl:choose>
      <xsl:when test="$target='data' or $target='config' or
                      $target='get-reply' or $target='get-config-reply'">
        <xsl:apply-templates select="descendant::nma:data">
          <xsl:with-param name="prefix" select="$prefix"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:when test="$target='rpc'">
        <xsl:apply-templates select="descendant::nma:input">
          <xsl:with-param name="prefix" select="$prefix"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:when test="$target='rpc-reply'">
        <xsl:apply-templates select="descendant::nma:output">
          <xsl:with-param name="prefix" select="$prefix"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:when test="$target='notification'">
        <xsl:apply-templates select="descendant::nma:notification">
          <xsl:with-param name="prefix" select="$prefix"/>
        </xsl:apply-templates>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:element[@nma:default]">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:param name="prefix"/>
    <xsl:call-template name="element-map">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
      <xsl:with-param name="content" select="@nma:default"/>
      <xsl:with-param name="case"
                      select="parent::rng:choice|../parent::rng:group|
                              ../parent::rng:interleave"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="rng:element[@nma:implicit='true']">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:param name="prefix"/>
    <xsl:call-template name="element-map">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
      <xsl:with-param name="content" select="rng:*"/>
      <xsl:with-param name="case"
                      select="parent::rng:choice|../parent::rng:group|
                              ../parent::rng:interleave"/>
    </xsl:call-template>
    <xsl:apply-templates select="rng:*">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template
      match="rng:choice/rng:group[not(@nma:implicit='true')]
             /rng:optional/rng:element|
             rng:choice/rng:interleave[not(@nma:implicit='true')]
             /rng:optional/rng:element">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:param name="prefix"/>
    <xsl:apply-templates select="rng:*">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template
      match="rng:choice/rng:group[not(@nma:implicit='true')]|
             rng:choice/rng:interleave[not(@nma:implicit='true')]"
      mode="copy"/>

  <xsl:template match="rng:element[@nma:implicit='true']" mode="copy">
    <xsl:param name="prefix"/>
    <xsl:variable name="name">
      <xsl:call-template name="qname">
        <xsl:with-param name="prefix" select="$prefix"/>
        <xsl:with-param name="name" select="@name"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:element name="{$name}"
                 namespace="{namespace::*[name()=$prefix]}">
      <xsl:apply-templates select="rng:*" mode="copy">
        <xsl:with-param name="prefix" select="$prefix"/>
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:element[@nma:default]" mode="copy">
    <xsl:param name="prefix"/>
    <xsl:variable name="name">
      <xsl:call-template name="qname">
        <xsl:with-param name="prefix" select="$prefix"/>
        <xsl:with-param name="name" select="@name"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="act-prefix">
      <xsl:choose>
	<xsl:when test="contains(@name,':')">
	  <xsl:value-of select="substring-before(@name,':')"/>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:value-of select="$prefix"/>
	</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:element name="{$name}"
                 namespace="{namespace::*[name()=$act-prefix]}">
      <xsl:value-of select="@nma:default"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:ref[@name='__anyxml__']"/>

  <xsl:template match="rng:*">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:param name="prefix"/>
    <xsl:apply-templates select="rng:*">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:ref">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:param name="prefix"/>
    <xsl:apply-templates select="//rng:define[@name=current()/@name]">
      <xsl:with-param name="prevpath">
        <xsl:call-template name="parent-path">
          <xsl:with-param name="prevpath" select="$prevpath"/>
          <xsl:with-param name="prefix" select="$prefix"/>
        </xsl:call-template>
      </xsl:with-param>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element|rng:data" mode="copy"/>

  <xsl:template match="rng:ref" mode="copy">
    <xsl:param name="prefix"/>
    <xsl:apply-templates select="//rng:define[@name=current()/@name]"
                         mode="copy">
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:define[@nma:default]" mode="copy">
    <xsl:value-of select="@nma:default"/>
  </xsl:template>

  <xsl:template match="rng:*" mode="copy">
    <xsl:param name="prefix"/>
    <xsl:apply-templates select="rng:*" mode="copy">
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

</xsl:stylesheet>
