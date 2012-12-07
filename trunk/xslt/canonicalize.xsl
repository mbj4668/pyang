<?xml version="1.0" encoding="utf-8"?>
<!-- Program name: canonicalize.xsl

Copyright © 2012 by Ladislav Lhotka, CZ.NIC <lhotka@nic.cz>

This stylesheet rearranges a YIN module into canonical order [RFC 6020].

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
		xmlns:xi="http://www.w3.org/2001/XInclude"
		xmlns:html="http://www.w3.org/1999/xhtml"
		xmlns:yin="urn:ietf:params:xml:ns:yang:yin:1"
		version="1.0">
  <xsl:output method="xml" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>
  <xsl:template name="preceding-comment">
    <xsl:if
	test="count((preceding-sibling::*|preceding-sibling::comment())
	      [last()]|preceding-sibling::comment()[1]) = 1">
      <xsl:apply-templates select="preceding-sibling::comment()[1]"/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="html:*|xi:*|@*|comment()|text()">
    <xsl:copy-of select="."/>
  </xsl:template>
  <xsl:template name="data-def-stmt">
    <xsl:apply-templates
	select="yin:container|yin:leaf|yin:leaf-list|
		yin:list|yin:choice|yin:anyxml|yin:uses"/>
  </xsl:template>

  <xsl:template match="yin:module">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:yang-version"/>
      <xsl:apply-templates select="yin:namespace"/>
      <xsl:apply-templates select="yin:prefix"/>
      <xsl:apply-templates select="yin:import"/>
      <xsl:apply-templates select="yin:include"/>
      <xsl:apply-templates select="yin:organization"/>
      <xsl:apply-templates select="yin:contact"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:revision"/>
      <xsl:apply-templates
	  select="yin:extension|yin:feature|yin:identity|yin:typedef|
		  yin:grouping|yin:container|yin:leaf|yin:leaf-list|
		  yin:list|yin:choice|yin:anyxml|yin:uses|yin:augment|
		  yin:rpc|yin:notification|yin:deviation"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:submodule">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:yang-version"/>
      <xsl:apply-templates select="yin:belongs-to"/>
      <xsl:apply-templates select="yin:import"/>
      <xsl:apply-templates select="yin:include"/>
      <xsl:apply-templates select="yin:organization"/>
      <xsl:apply-templates select="yin:contact"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:revision"/>
      <xsl:apply-templates
	  select="yin:extension|yin:feature|yin:identity|yin:typedef|
		  yin:grouping|yin:container|yin:leaf|yin:leaf-list|
		  yin:list|yin:choice|yin:anyxml|yin:uses|yin:augment|
		  yin:rpc|yin:notification|yin:deviation"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:feature">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:if-feature">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:identity">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:base"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:base">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:yang-version">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:import">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:prefix"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:include">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:namespace">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:prefix">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:belongs-to">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:prefix"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:organization">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:text"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:text">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:contact">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:text"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:description">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:text"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:reference">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:text"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:units">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:revision">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:extension">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:argument"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:argument">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:yin-element"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:yin-element">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:typedef">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:type"/>
      <xsl:apply-templates select="yin:units"/>
      <xsl:apply-templates select="yin:default"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:type">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:fraction-digits"/>
      <xsl:apply-templates select="yin:range"/>
      <xsl:apply-templates select="yin:length"/>
      <xsl:apply-templates select="yin:pattern"/>
      <xsl:apply-templates select="yin:enum"/>
      <xsl:apply-templates select="yin:bit"/>
      <xsl:apply-templates select="yin:path"/>
      <xsl:apply-templates select="yin:base"/>
      <xsl:apply-templates select="yin:type"/>
      <xsl:apply-templates select="yin:require-instance"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:fraction-digits">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:range">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:error-message"/>
      <xsl:apply-templates select="yin:error-app-tag"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:length">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:error-message"/>
      <xsl:apply-templates select="yin:error-app-tag"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:pattern">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:error-message"/>
      <xsl:apply-templates select="yin:error-app-tag"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:default">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:enum">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:value"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:bit">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:position"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:position">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:path">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:require-instance">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:status">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:config">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:mandatory">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:presence">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:ordered-by">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:must">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:error-message"/>
      <xsl:apply-templates select="yin:error-app-tag"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:error-message">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:value"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:value">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:error-app-tag">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:min-elements">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:max-elements">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:value">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:grouping">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:container">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:presence"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:leaf">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:type"/>
      <xsl:apply-templates select="yin:units"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:default"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:mandatory"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:leaf-list">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:type"/>
      <xsl:apply-templates select="yin:units"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:min-elements"/>
      <xsl:apply-templates select="yin:max-elements"/>
      <xsl:apply-templates select="yin:ordered-by"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:list">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:key"/>
      <xsl:apply-templates select="yin:unique"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:min-elements"/>
      <xsl:apply-templates select="yin:max-elements"/>
      <xsl:apply-templates select="yin:ordered-by"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:key">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:unique">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:choice">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:default"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:mandatory"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:container"/>
      <xsl:apply-templates select="yin:leaf"/>
      <xsl:apply-templates select="yin:leaf-list"/>
      <xsl:apply-templates select="yin:list"/>
      <xsl:apply-templates select="yin:anyxml"/>
      <xsl:apply-templates select="yin:case"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:case">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:anyxml">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:mandatory"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:uses">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:refine"/>
      <xsl:apply-templates select="yin:augment"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:refine">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:presence"/>
      <xsl:apply-templates select="yin:default"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:mandatory"/>
      <xsl:apply-templates select="yin:min-elements"/>
      <xsl:apply-templates select="yin:max-elements"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:augment">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:when"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:call-template name="data-def-stmt"/>
      <xsl:apply-templates select="yin:case"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:when">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:rpc">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:apply-templates select="yin:input"/>
      <xsl:apply-templates select="yin:output"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:input">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:output">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:notification">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:if-feature"/>
      <xsl:apply-templates select="yin:status"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:typedef"/>
      <xsl:apply-templates select="yin:grouping"/>
      <xsl:call-template name="data-def-stmt"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:deviation">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:description"/>
      <xsl:apply-templates select="yin:reference"/>
      <xsl:apply-templates select="yin:deviate"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="yin:deviate">
    <xsl:call-template name="preceding-comment"/>
    <xsl:copy>
      <xsl:apply-templates select="html:*|xi:*|@*|text()"/>
      <xsl:apply-templates select="yin:type"/>
      <xsl:apply-templates select="yin:units"/>
      <xsl:apply-templates select="yin:must"/>
      <xsl:apply-templates select="yin:unique"/>
      <xsl:apply-templates select="yin:default"/>
      <xsl:apply-templates select="yin:config"/>
      <xsl:apply-templates select="yin:mandatory"/>
      <xsl:apply-templates select="yin:min-elements"/>
      <xsl:apply-templates select="yin:max-elements"/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="/">
    <xsl:apply-templates select="yin:module"/>
    <xsl:apply-templates select="yin:submodule"/>
  </xsl:template>
</xsl:stylesheet>
