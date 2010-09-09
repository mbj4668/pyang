<?xml version="1.0" encoding="utf-8"?>

<!-- Program name: gen-common.xsl

Copyright © 2010 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Common templates for schema-generating stylesheets.

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
                version="1.0">

  <!-- String parameters -->

  <!-- Comma-separated list of unavailable features in the form
       <feature>@<module_name> (no spaces allowed), or the string
       '%' which means that NO feature is available -->
  <xsl:param name="off-features"/>
  <!-- Validation target: one of "datastore", "config-file",
       "get-reply", "get-config-reply", "rpc", "rpc-reply",
       "notification" -->
  <xsl:param name="target">datastore</xsl:param>
  <!-- If $only-data is nonzero, do not use the <nc:rpc-reply> element
       for "get-reply" and "get-config-reply" targets (i.e. <nc:data>
       is the document root). -->
  <xsl:param name="only-data" select="0"/>
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

  <!-- Namespace URIs -->
  <xsl:param name="rng-uri">http://relaxng.org/ns/structure/1.0</xsl:param>
  <xsl:param
      name="dtdc-uri">http://relaxng.org/ns/compatibility/annotations/1.0</xsl:param>
  <xsl:param name="dc-uri">http://purl.org/dc/terms</xsl:param>
  <xsl:param
      name="nma-uri">urn:ietf:params:xml:ns:netmod:dsdl-annotations:1</xsl:param>
  <xsl:param name="nc-uri">urn:ietf:params:xml:ns:netconf:base:1.0</xsl:param>
  <xsl:param name="en-uri">urn:ietf:params:xml:ns:netconf:notification:1.0</xsl:param>

  <xsl:variable name="netconf-part">
    <xsl:choose>
      <xsl:when test="$target='config-file'">
        <xsl:text>/nc:config</xsl:text>
      </xsl:when>
      <xsl:when
          test="$target='get-config-reply' or
                $target='get-reply'">
        <xsl:if test="$only-data=0">
          <xsl:text>/nc:rpc-reply</xsl:text>
        </xsl:if>
        <xsl:text>/nc:data</xsl:text>
      </xsl:when>
      <xsl:when test="$target='rpc'">
        <xsl:text>/nc:rpc</xsl:text>
      </xsl:when>
      <xsl:when test="$target='rpc-reply'">
        <xsl:text>/nc:rpc-reply</xsl:text>
      </xsl:when>
      <xsl:when test="$target='notification'">
        <xsl:text>/en:notification</xsl:text>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>

  <xsl:template name="check-input-pars">
    <xsl:if test="not($target='get-reply' or $target='datastore' or
                  $target='rpc' or $target='rpc-reply' or
                  $target='get-config-reply' or
                  $target='notification' or $target='config-file')">
      <xsl:message terminate="yes">
        <xsl:text>Bad 'target' parameter: </xsl:text>
        <xsl:value-of select="$target"/>
      </xsl:message>
    </xsl:if>
    <xsl:if test="($target='datastore' or starts-with($target,'get'))
                  and not(//nma:data/rng:*)">
      <xsl:message terminate="yes">
        <xsl:text>Data model defines no data.</xsl:text>
      </xsl:message>
    </xsl:if>
    <xsl:if test="($target='rpc' or $target='rpc-reply') and
                  not(//nma:rpc)">
      <xsl:message terminate="yes">
        <xsl:text>Data model defines no RPC methods.</xsl:text>
      </xsl:message>
    </xsl:if>
    <xsl:if test="$target='notification' and not(//nma:notification)">
      <xsl:message terminate="yes">
        <xsl:text>Data model defines no notifications.</xsl:text>
      </xsl:message>
    </xsl:if>
    <xsl:if test="not($gdefs-only='0' or $gdefs-only='1')">
      <xsl:message terminate="yes">
        <xsl:text>Bad 'gdefs-only' parameter value: </xsl:text>
        <xsl:value-of select="$gdefs-only"/>
      </xsl:message>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
