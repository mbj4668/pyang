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
                xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                xmlns:a="http://relaxng.org/ns/compatibility/annotations/1.0"                version="1.0">

  <xsl:include href="gen-common.xsl"/>

  <xsl:template name="ns-attribute">
    <xsl:if test="$target!='dstore'">
      <xsl:attribute name="ns">
	<xsl:choose>
	  <xsl:when test="$target='get-reply' or $target='getconf-reply'
			  or $target='rpc' or $target='rpc-reply'">
	    <xsl:text>urn:ietf:params:xml:ns:netconf:base:1.0</xsl:text>
	  </xsl:when>
	  <xsl:when test="$target='notif'">
	    <xsl:text>urn:ietf:params:xml:ns:netconf:notification:1.0</xsl:text>
	  </xsl:when>
	</xsl:choose>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>

  <xsl:template name="opt-choice">
    <xsl:param name="todo"/>
    <xsl:choose>
      <xsl:when test="count($todo)>1">
	<xsl:element name="rng:choice">
	  <xsl:apply-templates select="$todo"/>
	</xsl:element>
      </xsl:when>
      <xsl:otherwise>
	<xsl:apply-templates select="$todo"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/">
    <xsl:call-template name="check-input-pars"/>
    <xsl:choose>
      <xsl:when test="$gdefs-only=1">
	<xsl:apply-templates select="rng:grammar" mode="gdefs"/>
      </xsl:when>
      <xsl:otherwise>
	<xsl:apply-templates select="rng:grammar"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/rng:grammar" mode="gdefs">
    <xsl:element name="rng:grammar">
      <xsl:attribute name="datatypeLibrary">
	<xsl:value-of select="@datatypeLibrary"/>
      </xsl:attribute>
      <xsl:apply-templates select="rng:define"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="/rng:grammar">
    <xsl:copy>
      <xsl:apply-templates select="@*"/>
      <xsl:call-template name="ns-attribute"/>
      <xsl:element name="rng:include">
	<xsl:attribute name="href">
	  <xsl:value-of select="$rng-lib"/>
	</xsl:attribute>
      </xsl:element>
      <xsl:apply-templates select="rng:start"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="/rng:grammar/rng:start">
    <xsl:copy>
      <xsl:apply-templates select="rng:element[@name='nmt:netmod-tree']"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:netmod-tree']">
    <xsl:choose>
      <xsl:when test="$target='dstore'">
	<xsl:call-template name="opt-choice">
	  <xsl:with-param
	      name="todo"
	      select="rng:grammar[descendant::rng:element/@name='nmt:data']"/>
	</xsl:call-template>
      </xsl:when>
      <xsl:when test="$target='get-reply' or $target='getconf-reply'">
	<rng:element name="rpc-reply">
	  <rng:ref name="message-id-attribute"/>
	  <rng:element name="data">
	    <xsl:variable name="todo"
			  select="rng:grammar[descendant::rng:element/@name='nmt:data']"/>
	    <xsl:choose>
	      <xsl:when test="count($todo)>1">
		<xsl:element name="rng:interleave">
		  <xsl:apply-templates select="$todo"/>
		</xsl:element>
	      </xsl:when>
	      <xsl:otherwise>
		<xsl:apply-templates select="$todo"/>
	      </xsl:otherwise>
	    </xsl:choose>
	  </rng:element>
	</rng:element>
      </xsl:when>
      <xsl:when test="$target='rpc'">
        <rng:element name="rpc">
          <rng:ref name="message-id-attribute"/>
	  <xsl:call-template name="opt-choice">
	    <xsl:with-param
		name="todo"
		select="rng:grammar[descendant::rng:element/@name='nmt:input']"/>
	  </xsl:call-template>
	</rng:element>
      </xsl:when>
      <xsl:when test="$target='rpc-reply'">
        <rng:element name="rpc-reply">
          <rng:ref name="message-id-attribute"/>
	  <xsl:if test="$target='rpc-reply'
			and descendant::rpc-method[not(nmt:output)]">
	    <rng:ref name="ok-element"/>
	  </xsl:if>
	  <xsl:call-template name="opt-choice">
	    <xsl:with-param
		name="todo"
		select="rng:grammar[descendant::rng:element/@name='nmt:output']"/>
	  </xsl:call-template>
	</rng:element>
      </xsl:when>
      <xsl:when test="$target='notif'">
	<rng:element name="notification">
	  <rng:ref name="eventTime-element"/>
	  <xsl:call-template name="opt-choice">
	    <xsl:with-param
		name="todo"
		select="rng:grammar[descendant::rng:element/@name='nmt:notification']"/>
	  </xsl:call-template>
	</rng:element>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:grammar">
    <xsl:element name="rng:grammar">
      <xsl:attribute name="ns">
	<xsl:value-of select="@ns"/>
      </xsl:attribute>
      <xsl:if test="/rng:grammar/rng:define">
	<xsl:element name="rng:include">
	  <xsl:attribute name="href">
	    <xsl:value-of select="concat($basename,'-gdefs.rng')"/>
	  </xsl:attribute>
	</xsl:element>
      </xsl:if>
      <xsl:apply-templates select="rng:start"/>
      <xsl:apply-templates select="rng:define"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="rng:start">
    <xsl:copy>
      <xsl:choose>
	<xsl:when test="$target='dstore' or $target='get-reply'
			or $target='getconf-reply'">
	  <xsl:apply-templates select="rng:element[@name='nmt:data']"/>
	</xsl:when>
	<xsl:when test="$target='rpc'">
	  <xsl:apply-templates select="descendant::rng:element[@name='nmt:input']"/>
	</xsl:when>
	<xsl:when test="$target='rpc-reply'">
	  <xsl:apply-templates select="descendant::rng:element[@name='nmt:output']"/>
	</xsl:when>
	<xsl:when test="$target='notif'">
	  <xsl:apply-templates select="descendant::rng:element[@name='nmt:notification']"/>
	</xsl:when>
      </xsl:choose>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:data']">
    <xsl:choose>
      <xsl:when test="$target='dstore'">
	<xsl:call-template name="opt-choice">
	  <xsl:with-param name="todo" select="rng:*"/>
	</xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
	<xsl:apply-templates select="rng:*"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:element[@name='nmt:notification'
		       or @name='nmt:input' or @name='nmt:output']">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="@nma:*|nma:*|a:*"/>

  <xsl:template match="@*">
    <xsl:copy/>
  </xsl:template>

  <xsl:template match="rng:optional">
    <xsl:choose>
      <xsl:when test="$target='dstore' and
		      (parent::rng:element/@name='nmt:data' or
		      parent::rng:interleave/
		      parent::rng:element/@name='nmt:data')">
	<xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
	<xsl:copy>
	  <xsl:apply-templates/>
	</xsl:copy>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rng:*">
    <xsl:copy>
      <xsl:apply-templates select="@*"/>
      <xsl:choose>
        <xsl:when test="$target='getconf-reply'
                        and @nma:config='false'">
          <xsl:element name="rng:notAllowed"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates select="*|text()"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
