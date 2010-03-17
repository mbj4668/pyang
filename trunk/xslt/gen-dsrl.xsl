<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: gen-dsrl.xsl

Copyright © 2009 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Creates standalone DSRL schema from conceptual tree schema.

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

  <xsl:include href="gen-common.xsl"/>

  <!-- Namespace URIs -->
  <xsl:param name="rng-uri">http://relaxng.org/ns/structure/1.0</xsl:param>
  <xsl:param
      name="nmt-uri">urn:ietf:params:xml:ns:netmod:conceptual-tree:1</xsl:param>
  <xsl:param
      name="dtdc-uri">http://relaxng.org/ns/compatibility/annotations/1.0</xsl:param>
  <xsl:param name="dc-uri">http://purl.org/dc/terms</xsl:param>
  <xsl:param
      name="nma-uri">urn:ietf:params:xml:ns:netmod:dsdl-annotations:1</xsl:param>
  <xsl:param name="nc-uri">urn:ietf:params:xml:ns:netconf:base:1.0</xsl:param>
  <xsl:param name="en-uri">urn:ietf:params:xml:ns:netconf:notification:1.0</xsl:param>

  <xsl:variable name="netconf-part">
    <xsl:choose>
      <xsl:when
          test="$target='get-reply' or
                $target='getconf-reply'">/nc:rpc-reply/nc:data</xsl:when>
      <xsl:when test="$target='rpc'">/nc:rpc</xsl:when>
      <xsl:when test="$target='notif'">/en:notification</xsl:when>
    </xsl:choose>
  </xsl:variable>

  <xsl:template name="nc-namespace">
      <xsl:choose>
        <xsl:when test="$target='get-reply' or $target='getconf-reply'
                        or $target='rpc'">
          <xsl:variable name="dummy">
            <nc:dummy/>
          </xsl:variable>
          <xsl:copy-of select="exsl:node-set($dummy)/*/namespace::*"/>
        </xsl:when>
        <xsl:when test="$target='notif'">
          <xsl:variable name="dummy">
            <en:dummy/>
          </xsl:variable>
          <xsl:copy-of select="exsl:node-set($dummy)/namespace::*"/>
        </xsl:when>
      </xsl:choose>
  </xsl:template>

  <xsl:template name="parent-path">
    <xsl:param name="prevpath"/>
    <xsl:value-of select="$prevpath"/>
    <xsl:for-each select="ancestor::rng:element
                          [not(starts-with(@name,'nmt:'))]">
      <xsl:value-of select="concat('/',@name)"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="yam-namespaces">
    <xsl:for-each
        select="namespace::*[not(name()='xml' or .=$rng-uri or
                .=$nmt-uri or .=$dtdc-uri or .=$dc-uri or
                .=$nma-uri)]">
      <xsl:copy/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="element-map">
    <xsl:param name="prevpath"/>
    <xsl:param name="content"/>
    <xsl:param name="case" select="boolean(0)"/>
    <xsl:element name="dsrl:element-map">
      <xsl:element name="dsrl:parent">
        <xsl:call-template name="parent-path">
          <xsl:with-param name="prevpath" select="$prevpath"/>
        </xsl:call-template>
        <xsl:if test="$case">
          <xsl:apply-templates select="ancestor::rng:choice[1]"
                               mode="cases"/>
        </xsl:if>
      </xsl:element>
      <xsl:element name="dsrl:name">
        <xsl:value-of select="@name"/>
      </xsl:element>
      <xsl:element name="dsrl:default-content">
        <xsl:apply-templates select="$content" mode="copy"/>
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

  <xsl:template match="rng:grammar">
    <xsl:call-template name="yam-namespaces"/>
    <xsl:call-template name="nc-namespace"/>
    <xsl:apply-templates
        select="rng:start/rng:element[@name='nmt:netmod-tree']"/>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:netmod-tree']">
    <xsl:choose>
      <xsl:when test="$target='get-reply' or $target='getconf-reply'">
        <xsl:apply-templates select="rng:element[@name='nmt:top']"/>
      </xsl:when>
      <xsl:when test="$target='rpc'">
        <xsl:apply-templates select="key('rpc',$name)"/>
      </xsl:when>
      <xsl:when test="$target='notif'">
          <xsl:apply-templates
              select="rng:element[@name='nmt:notifications']/
                      rng:element[rng:element/@name=$name]"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:rpc-method']">
    <xsl:choose>
      <xsl:when test="$dir='input'">
        <xsl:apply-templates select="rng:element[@name='nmt:input']"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates
            select="rng:element[@name='nmt:output']"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:element[@nma:default]">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:call-template name="element-map">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="content" select="@nma:default"/>
      <xsl:with-param name="case"
                      select="parent::rng:choice|../parent::rng:group|
                              ../parent::rng:interleave"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="rng:element[@nma:implicit='true']">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:call-template name="element-map">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="content" select="rng:*"/>
      <xsl:with-param name="case"
                      select="parent::rng:choice|../parent::rng:group|
                              ../parent::rng:interleave"/>
    </xsl:call-template>
    <xsl:apply-templates select="rng:*">
      <xsl:with-param name="prevpath" select="$prevpath"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template
      match="rng:choice/rng:group[not(@nma:implicit='true')]
             /rng:optional/rng:element|
             rng:choice/rng:interleave[not(@nma:implicit='true')]
             /rng:optional/rng:element">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:apply-templates select="rng:*">
      <xsl:with-param name="prevpath" select="$prevpath"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template
      match="rng:choice/rng:group[not(@nma:implicit='true')]|
             rng:choice/rng:interleave[not(@nma:implicit='true')]"
      mode="copy"/>

  <xsl:template match="rng:element[@nma:implicit='true']" mode="copy">
    <xsl:element name="{@name}"
                 namespace="{namespace::*[name()=substring-before(
                            current()/@name,':')]}">
      <xsl:apply-templates select="rng:*" mode="copy"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:element[@nma:default]" mode="copy">
    <xsl:element name="{@name}"
                 namespace="{namespace::*[name()=substring-before(
                            current()/@name,':')]}">
      <xsl:value-of select="@nma:default"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:*">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:apply-templates select="rng:*">
      <xsl:with-param name="prevpath" select="$prevpath"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:ref">
    <xsl:param name="prevpath" select="$netconf-part"/>
    <xsl:apply-templates select="//rng:define[@name=current()/@name]">
      <xsl:with-param name="prevpath">
        <xsl:call-template name="parent-path">
          <xsl:with-param name="prevpath" select="$prevpath"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element|rng:data" mode="copy"/>

  <xsl:template match="rng:ref" mode="copy">
    <xsl:apply-templates select="//rng:define[@name=current()/@name]"
                         mode="copy"/>
  </xsl:template>

  <xsl:template match="rng:define[@nma:default]" mode="copy">
    <xsl:value-of select="@nma:default"/>
  </xsl:template>

  <xsl:template match="rng:*" mode="copy">
    <xsl:apply-templates select="rng:*" mode="copy"/>
  </xsl:template>

</xsl:stylesheet>
