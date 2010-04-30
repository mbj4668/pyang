<?xml version="1.0" encoding="utf-8"?>

<!-- Common templates for schema-generating stylesheets. -->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rng="http://relaxng.org/ns/structure/1.0"
                xmlns:nmt="urn:ietf:params:xml:ns:netmod:conceptual-tree:1"
                xmlns:nma="urn:ietf:params:xml:ns:netmod:dsdl-annotations:1"
                version="1.0">

  <xsl:output method="xml" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>

  <xsl:key name="rpc" match="//rng:element[@name='nmt:rpc-method']"
           use="rng:element[@name='nmt:input']/rng:element/@name"/>

  <!-- Command line parameters -->
  <!-- Validation target: one of "get-reply", "getconf-reply",
       "rpc", "notif" -->
  <xsl:param name="target">get-reply</xsl:param>
  <!-- RPC or notification name (including standard NS prefix) -->
  <xsl:param name="name"/>
  <!-- "input" -> RPC request, "output" -> RPC reply -->
  <xsl:param name="dir">input</xsl:param>
  <!-- Full path of the RELAX NG library file -->
  <xsl:param name="rng-lib">relaxng-lib.rng</xsl:param>
  <!-- Output of RELAX NG global defs only? -->
  <xsl:param name="gdefs-only" select="0"/>
  <!-- Base name of the output schemas -->
  <xsl:param name="basename">
    <xsl:for-each
	select="//rng:grammar/@nma:module">
      <xsl:value-of select="."/>
      <xsl:if test="position()!=last()">
	<xsl:text>_</xsl:text>
      </xsl:if>
    </xsl:for-each>
  </xsl:param>

  <xsl:template name="check-input-pars">
    <xsl:if test="not($target='get-reply' or $target='dstore' or $target='rpc'
                  or $target='getconf-reply' or $target='notif')">
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
    <xsl:if test="not($gdefs-only='0' or $gdefs-only='1')">
      <xsl:message terminate="yes">
	<xsl:text>Bad 'gdefs-only' parameter: </xsl:text>
	<xsl:value-of select="$gdefs-only"/>
      </xsl:message>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>

