<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: gen-schematron.xsl

Copyright © 2011 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Creates Schematron schema from the hybrid DSDL schema (see RFC 6110).

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

<!-- Edit the "annots" entity to select the annotations to take into
     account. -->
<!DOCTYPE stylesheet [
<!ENTITY annots "nma:must|nma:instance-identifier|@nma:key|@nma:unique|
@nma:max-elements|@nma:min-elements|@nma:when|@nma:leafref|@nma:leaf-list">
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rng="http://relaxng.org/ns/structure/1.0"
                xmlns:sch="http://purl.oclc.org/dsdl/schematron"
                xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                version="1.0">

  <xsl:output method="xml" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>

  <xsl:include href="gen-common.xsl"/>

  <xsl:key name="refdef" match="//rng:define" use="@name"/>

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

  <xsl:template name="report-element">
    <xsl:param name="test"/>
    <xsl:param name="message">
      <xsl:value-of
          select="concat('Violated condition &quot;', $test, '&quot;')"/>
    </xsl:param>
    <xsl:element name="sch:report">
      <xsl:attribute name="test">
        <xsl:value-of select="$test"/>
      </xsl:attribute>
      <xsl:value-of select="$message"/>
    </xsl:element>
  </xsl:template>

  <xsl:template name="nc-namespace">
    <xsl:choose>
      <xsl:when test="$target='config' or $target='get-reply' or
                      $target='get-config-reply' or $target='data'
                      or $target='rpc' or $target='rpc-reply'">
          <sch:ns uri="{$nc-uri}" prefix="nc"/>
      </xsl:when>
      <xsl:when test="$target='notification'">
          <sch:ns uri="{$en-uri}" prefix="en"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="qname">
    <xsl:param name="name"/>
    <xsl:if test="not(contains($name,':'))">$pref:</xsl:if>
    <xsl:value-of select="$name"/>
  </xsl:template>

  <xsl:template name="self-path">
    <xsl:param name="prevpath"/>
    <xsl:value-of select="$prevpath"/>
    <xsl:for-each select="ancestor-or-self::rng:element">
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
                .=$dtdc-uri or .=$dc-uri or .=$nma-uri)]">
      <sch:ns uri="{.}" prefix="{name()}"/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="uniq-expr-comp">
    <xsl:param name="key"/>
    <xsl:variable name="qkey">
      <xsl:call-template name="qname">
        <xsl:with-param name="name" select="$key"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="concat($qkey,'=current()/',$qkey)"/>
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

  <xsl:template name="mandatory-choice-rule">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:element name="sch:rule">
      <xsl:attribute name="context">
	<xsl:call-template name="self-path">
	  <xsl:with-param name="prevpath" select="$prevpath"/>
	  <xsl:with-param name="prefix" select="$prefix"/>
	</xsl:call-template>
      </xsl:attribute>
      <xsl:call-template name="assert-element">
	<xsl:with-param name="test">
	  <xsl:apply-templates select="." mode="lookup-subel">
	    <xsl:with-param name="prefix" select="$prefix"/>
	  </xsl:apply-templates>
	  <xsl:text>false()</xsl:text>
	</xsl:with-param>
	<xsl:with-param
	    name="message"
	    select="concat('Node(s) from one case of mandatory choice &quot;',
		    @nma:mandatory,'&quot; must exist')"/>
      </xsl:call-template>
    </xsl:element>
  </xsl:template>

  <xsl:template match="/">
    <xsl:call-template name="check-input-pars"/>
    <xsl:element name="sch:schema">
      <xsl:attribute name="queryBinding">exslt</xsl:attribute>
      <xsl:element name="sch:ns">
	<xsl:attribute name="uri">
	  <xsl:text>http://exslt.org/dynamic</xsl:text>
	</xsl:attribute>
	<xsl:attribute name="prefix">dyn</xsl:attribute>
      </xsl:element>
      <xsl:apply-templates select="rng:grammar"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="/rng:grammar">
      <xsl:call-template name="yam-namespaces"/>
      <xsl:call-template name="nc-namespace"/>
    <xsl:apply-templates
        select="rng:define[descendant-or-self::rng:*[&annots;]|
                descendant::rng:choice[@nma:mandatory]]"/>
    <xsl:apply-templates select="descendant::rng:grammar"/>
  </xsl:template>

  <xsl:template match="rng:define">
    <xsl:element name="sch:pattern">
      <xsl:attribute name="abstract">true</xsl:attribute>
      <xsl:attribute name="id">
        <xsl:value-of select="@name"/>
      </xsl:attribute>
      <xsl:apply-templates select="self::rng:define[&annots;]"
			   mode="annotdef"/>
      <xsl:apply-templates
          select="descendant::rng:element[&annots;]|
                  descendant::rng:choice[@nma:mandatory]">
        <xsl:with-param name="prevpath">$start</xsl:with-param>
        <xsl:with-param name="prefix">$pref</xsl:with-param>
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:define" mode="annotdef">
    <xsl:element name="sch:rule">
      <xsl:attribute name="context">$start</xsl:attribute>
      <xsl:apply-templates select="&annots;"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:grammar">
    <xsl:apply-templates
        select="rng:define[descendant-or-self::rng:*[&annots;]|
                descendant::rng:choice[@nma:mandatory]]"/>
    <xsl:choose>
      <xsl:when test="$target='data' or $target='config' or
                      $target='get-reply' or $target='get-config-reply'">
        <xsl:apply-templates select="descendant::nma:data"/>
      </xsl:when>
      <xsl:when test="$target='rpc'">
        <xsl:apply-templates select="descendant::nma:input"/>
      </xsl:when>
      <xsl:when test="$target='rpc-reply'">
        <xsl:apply-templates select="descendant::nma:output"/>
      </xsl:when>
      <xsl:when test="$target='notification'">
        <xsl:apply-templates select="descendant::nma:notification"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="nma:data|nma:input|nma:output|nma:notification">
    <xsl:variable
        name="prefix"
        select="name(namespace::*[.=ancestor::rng:grammar[1]/@ns])"/>
    <xsl:element name="sch:pattern">
      <xsl:attribute name="id">
        <xsl:value-of select="ancestor::rng:grammar[1]/@nma:module"/>
      </xsl:attribute>
      <xsl:apply-templates
          select="descendant::rng:element[&annots;]|
                  descendant::rng:choice[@nma:mandatory]">
        <xsl:with-param name="prevpath" select="$netconf-part"/>
        <xsl:with-param name="prefix" select="$prefix"/>
      </xsl:apply-templates>
    </xsl:element>
    <xsl:apply-templates
        mode="ref"
        select="rng:element|rng:optional|rng:choice|rng:group|rng:ref|
                rng:interleave|rng:zeroOrMore|rng:oneOrMore">
      <xsl:with-param name="prevpath" select="$netconf-part"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:element name="sch:rule">
      <xsl:attribute name="context">
      <xsl:call-template name="self-path">
        <xsl:with-param name="prevpath" select="$prevpath"/>
        <xsl:with-param name="prefix" select="$prefix"/>
      </xsl:call-template>
      </xsl:attribute>
      <xsl:apply-templates select="&annots;"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:choice[@nma:config='false']">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:if test="$target!='config' and $target!='get-config-reply'">
      <xsl:call-template name="mandatory-choice-rule">
	<xsl:with-param name="prevpath" select="$prevpath"/>
	<xsl:with-param name="prefix" select="$prefix"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <xsl:template match="rng:choice[@nma:if-feature]">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:if test="$features-off!=1">
      <xsl:call-template name="mandatory-choice-rule">
	<xsl:with-param name="prevpath" select="$prevpath"/>
	<xsl:with-param name="prefix" select="$prefix"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <xsl:template match="rng:choice">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:call-template name="mandatory-choice-rule">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="rng:element" mode="lookup-subel">
    <xsl:param name="prefix"/>
    <xsl:choose>
      <xsl:when test="contains(@name, ':')">
        <xsl:value-of select="concat(@name, ' or ')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="concat($prefix, ':', @name, ' or ')"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:ref" mode="lookup-subel">
    <xsl:param name="prefix"/>
    <xsl:apply-templates select="key('refdef', @name)" mode="lookup-subel">
        <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:*" mode="lookup-subel">
    <xsl:param name="prefix"/>
    <xsl:apply-templates
        mode="lookup-subel"
        select="rng:element|rng:optional|rng:choice|rng:group|rng:ref|
                rng:interleave|rng:zeroOrMore|rng:oneOrMore">
        <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:ref[@name='__anyxml__']" mode="ref"/>

  <xsl:template match="rng:ref" mode="ref">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:if
	test="key('refdef',@name)[descendant-or-self::rng:*[&annots;]|
                  descendant::rng:choice[@nma:mandatory]]">
      <xsl:element name="sch:pattern">
        <xsl:attribute name="id">
          <xsl:value-of select="generate-id()"/>
        </xsl:attribute>
        <xsl:attribute name="is-a">
          <xsl:value-of select="@name"/>
        </xsl:attribute>
        <xsl:element name="sch:param">
          <xsl:attribute name="name">start</xsl:attribute>
          <xsl:attribute name="value">
            <xsl:value-of select="$prevpath"/>
          </xsl:attribute>
        </xsl:element>
        <xsl:element name="sch:param">
          <xsl:attribute name="name">pref</xsl:attribute>
          <xsl:attribute name="value">
            <xsl:value-of select="$prefix"/>
          </xsl:attribute>
        </xsl:element>
      </xsl:element>
    </xsl:if>
    <xsl:apply-templates select="key('refdef',@name)" mode="ref">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:element" mode="ref">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:apply-templates
        mode="ref"
        select="rng:element|rng:optional|rng:choice|rng:group|rng:ref|
                rng:interleave|rng:zeroOrMore|rng:oneOrMore">
      <xsl:with-param name="prevpath">
        <xsl:value-of select="concat($prevpath,'/')"/>
        <xsl:call-template name="qname">
          <xsl:with-param name="name" select="@name"/>
        </xsl:call-template>
      </xsl:with-param>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:define" mode="ref">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:apply-templates
        mode="ref"
        select="rng:element|rng:optional|rng:choice|rng:group|rng:ref|
                rng:interleave|rng:zeroOrMore|rng:oneOrMore">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template match="rng:*" mode="ref">
    <xsl:param name="prevpath"/>
    <xsl:param name="prefix"/>
    <xsl:apply-templates
        mode="ref"
        select="rng:element|rng:optional|rng:choice|rng:group|rng:ref|
                rng:interleave|rng:zeroOrMore|rng:oneOrMore">
      <xsl:with-param name="prevpath" select="$prevpath"/>
      <xsl:with-param name="prefix" select="$prefix"/>
    </xsl:apply-templates>
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

  <xsl:template match="nma:instance-identifier">
    <xsl:if test="not(@require-instance='false')">
      <xsl:variable name="beg">
	<xsl:if test="starts-with(.,'/')">
	  <xsl:value-of select="$netconf-part"/>
	</xsl:if>
      </xsl:variable>
      <xsl:call-template name="assert-element">
	<xsl:with-param
	    name="test"
	    select="concat('dyn:evaluate(',$beg,.,')')"/>
	<xsl:with-param
	    name="message"
	    select="concat('The element pointed to by &quot;',
		    ../@name, '&quot; must exist')"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

  <xsl:template match="@nma:key">
    <xsl:call-template name="list-unique">
      <xsl:with-param
          name="message">Duplicate key</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="@nma:unique">
    <xsl:call-template name="list-unique">
      <xsl:with-param
          name="message">Violated uniqueness for</xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="list-unique">
    <xsl:param name="message"/>
    <xsl:element name="sch:report">
      <xsl:attribute name="test">
        <xsl:text>preceding-sibling::</xsl:text>
        <xsl:call-template name="qname">
          <xsl:with-param name="name" select="../@name"/>
        </xsl:call-template>
        <xsl:text>[</xsl:text>
        <xsl:call-template name="check-dup-expr">
          <xsl:with-param name="nodelist" select="."/>
        </xsl:call-template>
        <xsl:text>]</xsl:text>
      </xsl:attribute>
      <xsl:value-of select="concat($message, ' &quot;',.,'&quot;')"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="@nma:max-elements">
    <xsl:call-template name="assert-element">
      <xsl:with-param
          name="test"
          select="concat('count(../',../@name,')&lt;=',.,
                  ' or preceding-sibling::',../@name)"/>
      <xsl:with-param
          name="message"
          select="concat('Number of list items must be at most ',.)"/>
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
          select="."/>
      <xsl:with-param
          name="message"
          select="concat('Node &quot;', ../@name,
                  '&quot; is only valid when &quot;',.,'&quot;')"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="@nma:leafref">
    <xsl:variable name="beg">
      <xsl:if test="starts-with(.,'/')">
	<xsl:value-of select="$netconf-part"/>
      </xsl:if>
    </xsl:variable>
    <xsl:element name="sch:report">
      <xsl:attribute name="test">
        <xsl:value-of select="concat('not(',$beg,.,'=.)')"/>
      </xsl:attribute>
        <xsl:value-of
            select="concat('Leaf &quot;',.,
                    '&quot; does not exist for leafref value &quot;')"/>
        <xsl:element name="sch:value-of">
          <xsl:attribute name="select">.</xsl:attribute>
        </xsl:element>
        <xsl:text>&quot;</xsl:text>
    </xsl:element>
  </xsl:template>

  <xsl:template match="@nma:leaf-list[.='true']">
    <xsl:element name="sch:report">
      <xsl:attribute name="test">
        <xsl:text>. = preceding-sibling::</xsl:text>
        <xsl:call-template name="qname">
          <xsl:with-param name="name" select="../@name"/>
        </xsl:call-template>
      </xsl:attribute>
      <xsl:text>Duplicate leaf-list entry &quot;</xsl:text>
      <xsl:element name="sch:value-of">
        <xsl:attribute name="select">.</xsl:attribute>
      </xsl:element>
      <xsl:text>&quot;.</xsl:text>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
