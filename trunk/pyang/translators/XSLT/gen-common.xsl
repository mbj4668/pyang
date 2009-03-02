<?xml version="1.0" encoding="utf-8"?>

<!-- Common templates for schema-generating stylesheets. -->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
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
</xsl:stylesheet>

