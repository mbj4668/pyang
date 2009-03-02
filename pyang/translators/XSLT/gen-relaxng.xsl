<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: sep-relaxng.xsl

Copyright © 2009 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Creates standalone RELAX NG schema from conceptual tree schema.

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
                xmlns:nmt="urn:ietf:params:xml:ns:netmod:conceptual-tree:1"
                xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
                xmlns:en="urn:ietf:params:xml:ns:netconf:notification:1.0"
                version="1.0">

  <xsl:import href="gen-common.xsl"/>

  <xsl:template name="force-namespaces">
    <!-- Ugly hack to get the namespaces delared in the schema -->
    <xsl:choose>
      <xsl:when test="$target='get-reply' or $target='rpc'">
        <xsl:attribute name="nc:used">true</xsl:attribute>
      </xsl:when>
      <xsl:when test="$target='notif'">
        <xsl:attribute name="en:used">true</xsl:attribute>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/">
    <xsl:call-template name="check-input-pars"/>
    <xsl:apply-templates select="rng:grammar"/>
  </xsl:template>

  <xsl:template match="rng:grammar">
    <xsl:copy>
      <xsl:apply-templates select="@*"/>
      <xsl:element name="rng:include">
        <xsl:attribute name="href">
          <xsl:value-of select="$rng-lib"/>
        </xsl:attribute>
      </xsl:element>
      <xsl:apply-templates select="rng:*"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="rng:start">
    <xsl:copy>
      <xsl:call-template name="force-namespaces"/>
      <xsl:apply-templates select="rng:element[@name='nmt:netmod-tree']"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:netmod-tree']">
    <xsl:choose>
      <xsl:when test="$target='get-reply'">
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

  <xsl:template match="rng:element[@name='nmt:top']">
    <rng:element name="nc:rpc-reply">
      <rng:ref name="message-id-attribute"/>
      <rng:element name="nc:data">
        <xsl:apply-templates/>
      </rng:element>
    </rng:element>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:rpc-method']">
    <xsl:choose>
      <xsl:when test="$dir='input'">
        <rng:element name="nc:rpc">
          <rng:ref name="message-id-attribute"/>
          <xsl:apply-templates
              select="rng:element[@name='nmt:input']/*"/>
        </rng:element>
      </xsl:when>
      <xsl:otherwise>
        <rng:element name="nc:rpc-reply">
          <rng:ref name="message-id-attribute"/>
          <xsl:choose>
            <xsl:when test="rng:element[@name='nmt:output']">
              <xsl:apply-templates
                  select="rng:element[@name='nmt:output']/*"/>
            </xsl:when>
            <xsl:otherwise>
              <rng:ref name="ok-element"/>
            </xsl:otherwise>
          </xsl:choose>
        </rng:element>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="rng:element[@name='nmt:notification']">
    <rng:element name="en:notification">
      <rng:ref name="eventTime-element"/>
      <xsl:apply-templates/>
    </rng:element>
  </xsl:template>

  <xsl:template match="@nma:*"/>

  <xsl:template match="@*">
    <xsl:copy/>
  </xsl:template>

  <xsl:template match="rng:*">
    <xsl:copy>
      <xsl:apply-templates select="*|@*|text()"/>
    </xsl:copy>
  </xsl:template> 

</xsl:stylesheet>
