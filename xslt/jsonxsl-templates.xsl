<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
		version="1.0">

  <xsl:template name="commaq">
    <xsl:if test="following-sibling::*[name() != name(current())
		  and name() != name(preceding-sibling::*)]">
      <xsl:text>, </xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template name="escape-char">
    <xsl:param name="char"/>
    <xsl:param name="echar"/>
    <xsl:param name="text"/>
    <xsl:choose>
      <xsl:when test="contains($text,$char)">
	<xsl:value-of
	    select="concat(substring-before($text,$char),'\',$echar)"/>
	<xsl:call-template name="escape-char">
	  <xsl:with-param name="char" select="$char"/>
	  <xsl:with-param name="echar" select="$echar"/>
	  <xsl:with-param name="text"
			  select="substring-after($text,$char)"/>
	</xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
	<xsl:value-of select="$text"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="escape-text">
    <xsl:call-template name="escape-char">
      <xsl:with-param name="char" select="'&#xD;'"/>
      <xsl:with-param name="echar" select="'r'"/>
      <xsl:with-param name="text">
	<xsl:call-template name="escape-char">
	  <xsl:with-param name="char" select="'&#x9;'"/>
	  <xsl:with-param name="echar" select="'t'"/>
	  <xsl:with-param name="text">
	    <xsl:call-template name="escape-char">
	      <xsl:with-param name="char" select="'&#xA;'"/>
	      <xsl:with-param name="echar" select="'n'"/>
	      <xsl:with-param name="text">
		<xsl:call-template name="escape-char">
		  <xsl:with-param name="char" select="'&quot;'"/>
		  <xsl:with-param name="echar" select="'&quot;'"/>
		  <xsl:with-param name="text">
		    <xsl:call-template name="escape-char">
		      <xsl:with-param name="char" select="'\'"/>
		      <xsl:with-param name="echar" select="'\'"/>
		      <xsl:with-param name="text" select="."/>
		    </xsl:call-template>
		  </xsl:with-param>
		</xsl:call-template>
	      </xsl:with-param>
	    </xsl:call-template>
	  </xsl:with-param>
	</xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="object-name">
    <xsl:param name="nsid"/>
    <xsl:value-of select="concat('&quot;', $nsid, local-name(.), '&quot;: ')"/>
  </xsl:template>

  <xsl:template name="json-object">
    <xsl:text>{</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <xsl:template name="json-value">
    <xsl:param name="type">string</xsl:param>
    <xsl:choose>
      <xsl:when test="$type='unquoted'">
	<xsl:value-of select="normalize-space(.)"/>
      </xsl:when>
      <xsl:when test="$type='empty'">
	<xsl:text>[null]</xsl:text>
      </xsl:when>
      <xsl:when test="$type='string'">
	<xsl:text>"</xsl:text>
	<xsl:call-template name="escape-text"/>
	<xsl:text>"</xsl:text>
      </xsl:when>
      <xsl:when test="$type='other'">
	<xsl:value-of select="concat('&quot;', normalize-space(.),'&quot;')"/>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="container">
    <xsl:param name="nsid"/>
    <xsl:value-of
	select="concat('&quot;', $nsid, local-name(.), '&quot;: ')"/>
    <xsl:call-template name="json-object"/>
    <xsl:call-template name="commaq"/>
  </xsl:template>

  <xsl:template name="leaf">
    <xsl:param name="type"/>
    <xsl:param name="nsid"/>
    <xsl:value-of
	select="concat('&quot;', $nsid, local-name(.), '&quot;: ')"/>
    <xsl:call-template name="json-value">
      <xsl:with-param name="type" select="$type"/>
    </xsl:call-template>
    <xsl:call-template name="commaq"/>
  </xsl:template>

  <xsl:template name="leaf-list">
    <xsl:param name="type"/>
    <xsl:param name="nsid"/>
    <xsl:if test="not(preceding-sibling::*[name()=name(current())])">
      <xsl:value-of
	  select="concat('&quot;', $nsid, local-name(.), '&quot;: [')"/>
      <xsl:for-each select="../*[name()=name(current())]">
	<xsl:call-template name="json-value">
	  <xsl:with-param name="type" select="$type"/>
	</xsl:call-template>
	<xsl:if test="position() != last()">
	  <xsl:text>, </xsl:text>
	</xsl:if>
      </xsl:for-each>
      <xsl:text>]</xsl:text>
      <xsl:call-template name="commaq"/>
    </xsl:if>
  </xsl:template>

  <xsl:template name="list">
    <xsl:param name="nsid"/>
    <xsl:if test="not(preceding-sibling::*[name()=name(current())])">
      <xsl:value-of
	  select="concat('&quot;', $nsid, local-name(.), '&quot;: [')"/>
      <xsl:for-each select="../*[name()=name(current())]">
	<xsl:call-template name="json-object"/>
	<xsl:if test="position() != last()">
	  <xsl:text>, </xsl:text>
	</xsl:if>
      </xsl:for-each>
      <xsl:text>]</xsl:text>
      <xsl:call-template name="commaq"/>
    </xsl:if>
  </xsl:template>

  <xsl:template name="anyxml">
    <xsl:param name="nsid"/>
    <xsl:value-of
	select="concat('&quot;', $nsid, local-name(.), '&quot;: ')"/>
    <xsl:text>{</xsl:text>
    <xsl:apply-templates mode="anyxml"/>
    <xsl:text>}</xsl:text>
    <xsl:call-template name="commaq"/>
  </xsl:template>

  <xsl:template match="*" mode="anyxml">
    <xsl:if test="not(preceding-sibling::*[name()=name(current())])">
      <xsl:value-of
	  select="concat('&quot;', local-name(.), '&quot;: ')"/>
      <xsl:choose>
	<xsl:when test="following-sibling::*[name()=name(current())]">
	  <xsl:text>[</xsl:text>
	  <xsl:for-each select="../*[name()=name(current())]">
	    <xsl:choose>
	      <xsl:when test="*">
		<xsl:text>{</xsl:text>
		<xsl:apply-templates mode="anyxml"/>
		<xsl:text>}</xsl:text>
	      </xsl:when>
	      <xsl:otherwise>
		<xsl:call-template name="json-value"/>
	      </xsl:otherwise>
	    </xsl:choose>
	    <xsl:if test="position() != last()">
	      <xsl:text>, </xsl:text>
	    </xsl:if>
	  </xsl:for-each>
	  <xsl:text>]</xsl:text>
	</xsl:when>
	<xsl:when test="*">
	  <xsl:text>{</xsl:text>
	  <xsl:apply-templates mode="anyxml"/>
	  <xsl:text>}</xsl:text>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:call-template name="json-value"/>
	</xsl:otherwise>
      </xsl:choose>
      <xsl:call-template name="commaq"/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="@*|text()|comment()|processing-instruction()" mode="anyxml"/>

  <xsl:template match="/nc:data">
    <xsl:text>{</xsl:text>
    <xsl:apply-templates select="*"/>
    <xsl:text>}</xsl:text>
  </xsl:template>

  <xsl:template match="*">
    <xsl:message terminate="yes">
      <xsl:value-of select="concat('Aborting, bad element: ', name())"/>
    </xsl:message>
  </xsl:template>

</xsl:stylesheet>
