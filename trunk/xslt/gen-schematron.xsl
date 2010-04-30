<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: gen-schematron.xsl

Copyright © 2010 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

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
<!ENTITY annots "nma:must|@nma:key|@nma:unique|@nma:max-elements|
@nma:min-elements|@nma:when|@nma:leafref">
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rng="http://relaxng.org/ns/structure/1.0"
                xmlns:sch="http://purl.oclc.org/dsdl/schematron"
                xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                version="1.0">

  <xsl:include href="gen-common.xsl"/>

  <xsl:key name="refdef" match="//rng:define" use="@name"/>

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

  <xsl:template name="assert-element">
    <xsl:param name="test"/>
    <xsl:param name="message">
      <xsl:value-of
          select="concat('Condition &quot;', $test, '&quot; must be true')"/>
    </xsl:param>
    <xsl:element name="sch:assert">
      <xsl:attribute name="test">
        <xsl:value-of select="$test"/>
      </xsl:attribute>
      <xsl:value-of select="$message"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="netconf-part">
    <xsl:choose>
      <xsl:when
          test="$target='get-reply' or
                $target='getconf-reply'">/nc:rpc-reply/nc:data</xsl:when>
      <xsl:when test="$target='rpc'">/nc:rpc</xsl:when>
      <xsl:when test="$target='rpc-reply'">/nc:rpc-reply</xsl:when>
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

  <xsl:template name="qname">
    <xsl:param name="name"/>
    <xsl:if test="not(contains($name,':'))">$pref:</xsl:if>
    <xsl:value-of select="$name"/>
  </xsl:template>

  <xsl:template name="append-path">
    <!-- Concat $start and XPath of the context element in the data tree -->
    <xsl:param name="start"/>
    <xsl:value-of select="$start"/>
    <xsl:for-each select="ancestor-or-self::rng:element
                          [not(starts-with(@name,'nmt:'))]">
      <xsl:text>/</xsl:text>
      <xsl:call-template name="qname">
	<xsl:with-param name="name" select="@name"/>
      </xsl:call-template>
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

  <xsl:template name="uniq-expr-comp">
    <xsl:param name="key"/>
    <xsl:value-of select="concat($key,'=current()/',$key)"/>
  </xsl:template>

  <xsl:template name="check-dup-expr">
    <xsl:param name="nodelist"/>
    <xsl:choose>
      <xsl:when test="contains($nodelist,' ')">
        <xsl:call-template name="uniq-expr-comp">
          <xsl:with-param name="key"
                          select="substring-before($nodelist, ' ')"/>
        </xsl:call-template>
        <xsl:text> and </xsl:text>
        <xsl:call-template name="check-dup-expr">
          <xsl:with-param name="nodelist"
                          select="substring-after($nodelist,' ')"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>  <!-- just one node -->
        <xsl:call-template name="uniq-expr-comp">
          <xsl:with-param name="key"
                          select="$nodelist"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/">
    <xsl:call-template name="check-input-pars"/>
    <xsl:element name="sch:schema">
      <xsl:apply-templates select="rng:grammar"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="/rng:grammar">
      <xsl:call-template name="yam-namespaces"/>
      <xsl:call-template name="nc-namespace"/>
    <xsl:apply-templates
	select="rng:define[descendant::rng:element[&annots;]]"/>
    <xsl:apply-templates select="descendant::rng:grammar"/>
  </xsl:template>

  <xsl:template match="rng:define">
    <xsl:element name="sch:pattern">
      <xsl:attribute name="abstract">true</xsl:attribute>
      <xsl:attribute name="id">
	<xsl:value-of select="@name"/>
      </xsl:attribute>
      <xsl:apply-templates select="descendant::rng:element[&annots;]">
	<xsl:with-param name="start">$start</xsl:with-param>
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:grammar">
    <xsl:apply-templates
	select="rng:define[descendant::rng:element[&annots;]]"/>
    <xsl:choose>
      <xsl:when test="$target='dstore' or $target='get-reply'
		      or $target='getconf-reply'">
	<xsl:apply-templates
	    select="descendant::rng:element[@name='nmt:data']"/>
      </xsl:when>
      <xsl:when test="$target='rpc'">
	<xsl:apply-templates
	    select="descendant::rng:element[@name='nmt:input']"/>
      </xsl:when>
      <xsl:when test="$target='rpc-reply'">
	<xsl:apply-templates
	    select="descendant::rng:element[@name='nmt:output']"/>
      </xsl:when>
      <xsl:when test="$target='notif'">
	<xsl:apply-templates
	    select="descendant::rng:element[@name='nmt:notification']"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:element[starts-with(@name,'nmt:')]">
    <xsl:element name="sch:pattern">
      <xsl:attribute name="id">
	<xsl:value-of select="ancestor::rng:grammar/@nma:module"/>
      </xsl:attribute>
      <xsl:apply-templates select="descendant::rng:element[&annots;]">
	<xsl:with-param name="start">
	  <xsl:call-template name="netconf-part"/>
	</xsl:with-param>
      </xsl:apply-templates>
    </xsl:element>
    <xsl:apply-templates select="rng:element|rng:ref" mode="ref">
      <xsl:with-param name="start">
	<xsl:call-template name="netconf-part"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element">
    <xsl:param name="start"/>
    <xsl:element name="sch:rule">
      <xsl:attribute name="context">
      <xsl:call-template name="append-path">
	<xsl:with-param name="start" select="$start"/>
      </xsl:call-template>
      </xsl:attribute>
      <xsl:apply-templates select="&annots;"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:ref" mode="ref">
    <xsl:param name="start"/>
    <xsl:if test="key('refdef',@name)/descendant::rng:element[&annots;]">
      <xsl:element name="sch:pattern">
	<xsl:attribute name="is-a">
	  <xsl:value-of select="@name"/>
	</xsl:attribute>
	<xsl:element name="sch:param">
	  <xsl:attribute name="name">start</xsl:attribute>
	  <xsl:attribute name="value">
	    <xsl:value-of select="$start"/>
	  </xsl:attribute>
	</xsl:element>
	<xsl:element name="sch:param">
	  <xsl:attribute name="name">pref</xsl:attribute>
	  <xsl:attribute name="value">
	    <xsl:value-of
		select="name(namespace::*[.=current()/ancestor::rng:grammar[1]/@ns])"/>
	  </xsl:attribute>
	</xsl:element>
      </xsl:element>
    </xsl:if>
    <xsl:apply-templates select="key('refdef',.)" mode="ref">
      <xsl:with-param name="start" select="$start"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element" mode="ref">
    <xsl:param name="start"/>
    <xsl:apply-templates select="rng:ref|rng:element" mode="ref">
      <xsl:with-param name="start">
	<xsl:value-of select="concat($start,'/')"/>
	<xsl:call-template name="qname">
	  <xsl:with-param name="name" select="@name"/>
	</xsl:call-template>
      </xsl:with-param>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:define" mode="ref">
    <xsl:param name="start"/>
    <xsl:if test="descendant::rng:element[&annots;]">
    </xsl:if>
  </xsl:template>

  <xsl:template match="nma:must">
    <xsl:choose>
      <xsl:when test="nma:error-message">
        <xsl:call-template name="assert-element">
          <xsl:with-param name="test" select="@assert"/>
          <xsl:with-param name="message" select="nma:error-message"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="assert-element">
          <xsl:with-param name="test" select="@assert"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="@nma:key">
    <xsl:call-template name="list-unique">
      <xsl:with-param
          name="message">Duplicate key of list</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="@nma:unique">
    <xsl:call-template name="list-unique">
      <xsl:with-param
          name="message">Violated uniqueness for list</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="list-unique">
    <xsl:param name="message"/>
    <xsl:element name="sch:report">
      <xsl:attribute name="test">
        <xsl:value-of
            select="concat('preceding-sibling::',../@name,'[')"/>
        <xsl:call-template name="check-dup-expr">
          <xsl:with-param name="nodelist" select="."/>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
      </xsl:attribute>
      <xsl:value-of select="concat($message, ' ',../@name)"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="@nma:max-elements">
    <xsl:call-template name="assert-element">
      <xsl:with-param
          name="test"
          select="concat('count(../',../@name,')&lt;=',.)"/>
      <xsl:with-param
          name="message"
          select="concat('List &quot;',../@name,
                  '&quot; - item count must be at most ',.)"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="@nma:min-elements">
    <xsl:call-template name="assert-element">
      <xsl:with-param
          name="test"
          select="concat('count(../',../@name,')&gt;=',.)"/>
      <xsl:with-param
          name="message"
          select="concat('List &quot;',../@name,
                  '&quot; - item count must be at least ',.)"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="@nma:when">
    <xsl:call-template name="assert-element">
      <xsl:with-param
          name="test"
          select="concat('(',.,') or not(..)')"/>
      <xsl:with-param
          name="message"
          select="concat('Node &quot;',../@name,
                  '&quot; requires &quot;',.,'&quot;')"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="@nma:leafref">
    <xsl:call-template name="assert-element">
      <xsl:with-param name="test" select="concat(.,'=.')"/>
      <xsl:with-param
          name="message"
          select="concat('Leafref &quot;',../@name,
                  '&quot; must have the same value as &quot;',.,'&quot;')"/>
    </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>
