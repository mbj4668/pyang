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

  <xsl:template name="eat-quoted">
    <xsl:param name="text"/>
    <xsl:param name="qch">'</xsl:param>
    <xsl:value-of select="concat(substring-before($text,$qch),$qch)"/>
    <xsl:call-template name="eat-unquoted">
      <xsl:with-param name="text" select="substring-after($text,$qch)"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="eat-unquoted">
    <xsl:param name="text"/>
    <xsl:if test="string-length($text) &gt; 0">
      <xsl:variable name="first" select="substring($text,1,1)"/>
      <xsl:variable name="quotes">'"</xsl:variable>
      <xsl:value-of select="$first"/>
      <xsl:choose>
	<xsl:when test="$first='/' or $first='[' and
			string-length(substring-before($text,':'))
			&lt; string-length(substring-before($text,']'))">
	  <xsl:call-template name="translate-prefix">
	    <xsl:with-param name="prf" select="substring-before(substring($text,2),':')"/>
	  </xsl:call-template>
	  <xsl:call-template name="eat-unquoted">
	    <xsl:with-param name="text" select="substring-after($text,':')"/>
	  </xsl:call-template>
	</xsl:when>
	<xsl:when test="contains($quotes,$first)">
	  <xsl:call-template name="eat-quoted">
	    <xsl:with-param name="text" select="substring($text,2)"/>
	    <xsl:with-param name="qch" select="$first"/>
	  </xsl:call-template>
	</xsl:when>
	<xsl:otherwise>
	  <xsl:call-template name="eat-unquoted">
	    <xsl:with-param name="text" select="substring($text,2)"/>
	  </xsl:call-template>
	</xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

  <xsl:template name="translate-prefix">
    <xsl:param name="prf"/>
    <xsl:call-template name="nsuri-to-module">
      <xsl:with-param name="uri" select="namespace::*[name()=normalize-space($prf)]"/>
    </xsl:call-template>
    <xsl:text>:</xsl:text>
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
      <xsl:when test="$type='instance-identifier'">
	<xsl:variable name="cont" select="normalize-space(.)"/>
	<xsl:if test="not(starts-with($cont,'/'))">
	  <xsl:message terminate="yes">
	    <xsl:value-of
		select="concat('Wrong instance identifier: ', $cont)"/>
	  </xsl:message>
	</xsl:if>
	<xsl:text>"</xsl:text>
	<xsl:call-template name="eat-unquoted">
	  <xsl:with-param name="text" select="$cont"/>
	</xsl:call-template>
	<xsl:text>"</xsl:text>
      </xsl:when>
      <xsl:when test="$type='identityref'">
	<xsl:variable name="cont" select="normalize-space(.)"/>
	<xsl:text>"</xsl:text>
	<xsl:choose>
	  <xsl:when test="contains($cont,':')">
	    <xsl:call-template name="translate-prefix">
	      <xsl:with-param name="prf"
			      select="substring-before($cont,':')"/>
	    </xsl:call-template>
	    <xsl:value-of select="substring-after($cont, ':')"/>
	  </xsl:when>
	  <xsl:otherwise>
	    <xsl:value-of select="$cont"/>
	  </xsl:otherwise>
	</xsl:choose>
	<xsl:text>"</xsl:text>
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

  <xsl:template match="/">
    <xsl:apply-templates select="//nc:data|//nc:config"/>
  </xsl:template>

  <xsl:template match="nc:data|nc:config">
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
