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

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:rng="http://relaxng.org/ns/structure/1.0"
		xmlns:sch="http://purl.oclc.org/dsdl/schematron"
		xmlns:nmt="urn:ietf:params:xml:ns:netmod:conceptual-tree:1"
		xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                version="1.0">

  <xsl:output method="xml" encoding="utf-8"/>

  <!-- Command line parameters -->
  <xsl:param name="target">get-reply</xsl:param>
  <xsl:param name="name"/>
  <xsl:param name="dir">input</xsl:param>

  <!-- Namespace URIs to be ignored -->
  <xsl:param name="ns-rng">http://relaxng.org/ns/structure/1.0</xsl:param>
  <xsl:param
      name="ns-nmt">urn:ietf:params:xml:ns:netmod:conceptual-tree:1</xsl:param>
  <xsl:param
      name="ns-dtdc">http://relaxng.org/ns/compatibility/annotations/1.0</xsl:param>
  
  <xsl:param name="ns-dc">http://purl.org/dc/terms</xsl:param>
  <xsl:param
      name="ns-nma">urn:ietf:params:xml:ns:netmod:dsdl-annotations:1</xsl:param>

  <xsl:template name="check-input-pars">
    <xsl:if test="not($target='get-reply' or $target='rpc'
		  or $target='notif')">
      <xsl:message terminate="yes">
	<xsl:text>Bad 'target' parameter: </xsl:text>
	<xsl:value-of select="$target"/>
      </xsl:message>
    </xsl:if>
    <xsl:if test="($target='rpc' or $target='notif') and $name=''">
      <xsl:message terminate="yes">
	<xsl:text>Parameter 'name' must be supplied for target '</xsl:text>
	<xsl:value-of select="$target"/>
	<xsl:text>'</xsl:text>
      </xsl:message>
    </xsl:if>
    <xsl:if test="$target='notif'">
      <xsl:if test="not(//rng:element[@name='nmt:notification']/
		    rng:attribute[rng:value=$name])">
	<xsl:message terminate="yes">
	  <xsl:text>Notification not found: </xsl:text>
	  <xsl:value-of select="$name"/>
	</xsl:message>
      </xsl:if>
    </xsl:if>
    <xsl:if test="$target='rpc'">
      <xsl:if test="not(//rng:element[@name='nmt:rpc-method']/
		    rng:attribute[rng:value=$name])">
	<xsl:message terminate="yes">
	  <xsl:text>RPC method not found: </xsl:text>
	  <xsl:value-of select="$name"/>
	</xsl:message>
      </xsl:if>
      <xsl:if test="not($dir='input' or $dir='output')">
	<xsl:message terminate="yes">
	  <xsl:text>Bad 'dir' parameter: </xsl:text>
	  <xsl:value-of select="$dir"/>
	</xsl:message>
      </xsl:if>
    </xsl:if>
  </xsl:template>

  <xsl:template name="elem-path">
    <xsl:param name="tail"/>
    <xsl:variable name="anc"
		  select="ancestor::rng:define"/>
  </xsl:template>

  <xsl:template name="yam-namespaces">
    <xsl:for-each select="namespace::*[not(name()='xml' or .=$ns-rng or
			  .=$ns-nmt or .=$ns-dtdc or .=$ns-dc or .=$ns-nma)]">
      <xsl:element name="sch:ns">
	<xsl:attribute name="uri">
	  <xsl:value-of select="."/>
	</xsl:attribute>
	<xsl:attribute name="prefix">
	  <xsl:value-of select="name()"/>
	</xsl:attribute>
      </xsl:element>
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
    <xsl:apply-templates select="//rng:element[@name='nmt:netmod-tree']"/>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:netmod-tree']">
    <xsl:choose>
      <xsl:when test="$target='get-reply'">
	<xsl:apply-templates select="rng:element[@name='nmt:top']"/>
      </xsl:when>
      <xsl:when test="$target='rpc'">
	<xsl:apply-templates
	    select="rng:element[@name='nmt:rpc-methods']/
		    rng:element[rng:attribute/rng:value=$name]"/>
      </xsl:when>
      <xsl:when test="$target='notif'">
	<xsl:apply-templates
	    select="rng:element[@name='nmt:notifications']/
		    rng:element[rng:attribute/rng:value=$name]"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:top']">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:rpc-method']">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:notification']">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="rng:element">
    <xsl:element name="element">
      <xsl:attribute name="name">
	<xsl:value-of select="@name"/>
      </xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:ref">
    <xsl:apply-templates select="//rng:define[@name=current()/@name]"/>
  </xsl:template>

  <xsl:template match="rng:optional|rng:interleave|rng:choice|rng:define
		       |rng:zeroOrMore|rng:oneOrMore|rng:group">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="rng:*"/>	        <!-- ignore the rest -->

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
