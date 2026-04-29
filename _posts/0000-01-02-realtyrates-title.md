---
layout: slide
title: ""
slide-id: realtyrates-title
classes: [title-slide]
---

<div style="text-align:center; padding: 2rem 0;">
  <h1 style="font-size:2.4rem; margin-bottom:1rem;">Subdivision Analysis</h1>
  <h2 style="font-size:1.3rem; font-weight:400; color:#aaa; margin-bottom:2rem;">
    RealtyRates.com Free Survey Data
  </h2>
  <p style="color:#888; font-size:0.9rem;">
    {{ site.data.realtyrates.commercial_rates.quarter | default: "Latest Quarter" }} &nbsp;·&nbsp;
    Updated {{ site.data.realtyrates.metadata.last_updated | date: "%B %Y" }}
  </p>
  <hr style="margin:2rem auto; width:60%; border-color:#333;">
  <p style="color:#999; font-size:0.85rem;">
    Cap Rates &nbsp;·&nbsp; Developer Survey &nbsp;·&nbsp; Financial Indices
  </p>
</div>
