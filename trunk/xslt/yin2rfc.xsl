<?xml version="1.0"?>

<!-- Program name: yin2rfc.xsl

Copyright © 2011 by Ladislav Lhotka, CESNET <lhotka@cesnet.cz>

Translates YIN to YANG suitable for inclusion in xml2rfc source.

NOTES:

1. YANG source is enclosed in the <artwork> element and also uses the
   demarcating labels <CODE BEGIN> and <CODE END>. 

2. See the comments at the beginning of yinlib.xsl for details of the
   translation and supported extensions.

==

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
		xmlns:yin="urn:ietf:params:xml:ns:yang:yin:1"
		xmlns:html="http://www.w3.org/1999/xhtml"
		version="1.0">
  <xsl:strip-space elements="*"/>
  <xsl:output method="xml" omit-xml-declaration="yes"/>

  <xsl:include href="yinlib.xsl"/>

  <!-- Root element -->

  <xsl:template match="/">
    <xsl:element name="artwork">
      <xsl:text>&#xA;&lt;CODE BEGINS&gt; file "</xsl:text>
      <xsl:value-of
	  select="concat(/yin:module/@name,'@',$revision)"/>
      <xsl:text>"&#xA;&#xA;</xsl:text>
      <xsl:apply-templates
	  select="yin:module|yin:submodule|comment()"/>
      <xsl:text>&#xA;&lt;CODE ENDS&gt;</xsl:text>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
