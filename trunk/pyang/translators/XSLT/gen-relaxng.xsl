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

  <xsl:output method="xml" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>

  <xsl:key name="rpc" match="//rng:element[@name='nmt:rpc-method']"
	   use="rng:element[@name='nmt:input']/rng:element/@name"/>

  <!-- Command line parameters -->
  <!-- Validation target: one of "get-reply", "rpc", "notif" -->
  <xsl:param name="target">get-reply</xsl:param>
  <!-- RPC or notification name (including standard NS prefix) -->
  <xsl:param name="name"/>
  <!-- "input" -> RPC request, "output" -> RPC reply -->
  <xsl:param name="dir">input</xsl:param>
  <!-- Full path of the RELAX NG library file -->
  <xsl:param name="rng-lib">relaxng-lib.rng</xsl:param>

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
      <xsl:if test="not(//rng:element[@name='nmt:notification']
		    /rng:element[@name=$name])">
	<xsl:message terminate="yes">
	  <xsl:text>Notification not found: </xsl:text>
	  <xsl:value-of select="$name"/>
	</xsl:message>
      </xsl:if>
    </xsl:if>
    <xsl:if test="$target='rpc'">
      <xsl:if test="not(key('rpc',$name))">
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
