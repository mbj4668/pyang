<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: sep-schematron.xsl

Copyright © 2009 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Creates standalone Schematron schema from conceptual tree schema.

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
<!DOCTYPE xsl:stylesheet [
<!ENTITY elem-todo "descendant::rng:ref|
descendant::rng:element[nma:must]">
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:rng="http://relaxng.org/ns/structure/1.0"
		xmlns:sch="http://purl.oclc.org/dsdl/schematron"
		xmlns:nmt="urn:ietf:params:xml:ns:netmod:conceptual-tree:1"
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

  <xsl:template name="netconf-part">
    <xsl:choose>
      <xsl:when
	  test="$target='get-reply' or
		$target='getconf-reply'">/nc:rpc-reply/nc:data</xsl:when>
      <xsl:when test="$target='rpc'">/nc:rpc</xsl:when>
      <xsl:when test="$target='notif'">/en:notification</xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="nc-namespace">
    <xsl:choose>
      <xsl:when test="$target='get-reply' or $target='getconf-reply'
		      or $target='rpc'">
	  <sch:ns uri="{$nc-uri}" prefix="nc"/>
      </xsl:when>
      <xsl:when test="$target='notif'">
	  <sch:ns uri="{$en-uri}" prefix="en"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="append-path">
    <!-- Concat $start and XPath of the context element in the data tree -->
    <xsl:param name="start">
      <xsl:call-template name="netconf-part"/>
    </xsl:param>
    <xsl:value-of select="$start"/>
    <xsl:for-each select="ancestor-or-self::rng:element
			  [not(starts-with(@name,'nmt:'))]">
      <xsl:value-of select="concat('/',@name)"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="yam-namespaces">
    <!-- Make <ns> elements for all YANG module namespaces by
	 excluding others declared in the input schema -->
    <xsl:for-each
	select="namespace::*[not(name()='xml' or .=$rng-uri or
		.=$nmt-uri or .=$dtdc-uri or .=$dc-uri or
		.=$nma-uri)]">
      <sch:ns uri="{.}" prefix="{name()}"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="/">
    <xsl:call-template name="check-input-pars"/>
    <xsl:element name="sch:schema">
      <xsl:apply-templates select="rng:grammar"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:grammar">
    <xsl:call-template name="yam-namespaces"/>
    <xsl:call-template name="nc-namespace"/>
    <xsl:element name="sch:pattern">
      <xsl:apply-templates mode="abstract"
			   select="rng:define//rng:element[nma:must]"/>
      <!-- Template below is in gen-common.xsl -->
      <xsl:apply-templates
	  select="rng:start/rng:element[@name='nmt:netmod-tree']"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:top']">
    <xsl:apply-templates
	select="&elem-todo;"/>
  </xsl:template>

  <xsl:template match="rng:element" mode="abstract">
    <xsl:element name="sch:rule">
      <xsl:attribute name="id">
	<xsl:value-of select="generate-id()"/>
      </xsl:attribute>
      <xsl:attribute name="abstract">true</xsl:attribute>
      <xsl:apply-templates select="nma:must"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:element">
    <xsl:element name="sch:rule">
      <xsl:attribute name="context">
	<xsl:call-template name="append-path"/>
      </xsl:attribute>
      <xsl:apply-templates select="nma:must"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:ref">
    <xsl:apply-templates select="." mode="ref"/>
  </xsl:template>

  <xsl:template match="rng:ref" mode="ref">
    <xsl:param name="estart">
      <xsl:call-template name="netconf-part"/>
    </xsl:param>
    <xsl:apply-templates select="//rng:define[@name=current()/@name]">
      <xsl:with-param name="dstart">
	<xsl:call-template name="append-path">
	  <xsl:with-param name="start" select="$estart"/>
	</xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:define">
    <xsl:param name="dstart"/>
    <xsl:apply-templates select="&elem-todo;" mode="ref">
      <xsl:with-param name="estart" select="$dstart"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element" mode="ref">
    <xsl:param name="estart"/>
    <xsl:element name="sch:rule">
      <xsl:attribute name="context">
	<xsl:call-template name="append-path">
	  <xsl:with-param name="start" select="$estart"/>
	</xsl:call-template>
      </xsl:attribute>
      <xsl:element name="sch:extends">
	<xsl:attribute name="rule">
	  <xsl:value-of select="generate-id()"/>
	</xsl:attribute>
      </xsl:element>
    </xsl:element>
  </xsl:template>

  <xsl:template match="nma:must">
    <xsl:element name="sch:assert">
      <xsl:attribute name="test">
	<xsl:value-of select="@assert"/>
      </xsl:attribute>
      <xsl:choose>
	<xsl:when test="nma:error-message">
	  <xsl:value-of select="nma:error-message"/>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:value-of select="concat('Failed assert: ', @assert)"/>
	</xsl:otherwise>
      </xsl:choose>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
