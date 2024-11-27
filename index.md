---
layout: default
title: Home
---

<div class="section intro reveal">
    <h2 class="gradient-text">Biography</h2>

    <p>I am a Research Fellow at the <a href="https://yu-lab.hms.harvard.edu/" target="_blank">Yu Lab</a>, Harvard Medical School and Harvard University, working with Prof. <a href="https://scholar.google.com/citations?user=8EWwnDQAAAAJ" target="_blank">Kun-Hsing Yu</a>. Previously, I worked at the Medical Imaging and Signal Processing Laboratory (<a href="https://sites.google.com/view/mispl/home" target="_blank">MISPL</a>), Daegu Gyeongbuk Institute of Science and Technology with Prof. <a href="https://scholar.google.com/citations?user=M9u8pFEAAAAJ" target="_blank">Sang Hyun Park</a>.</p>

    <p>I received my Ph.D. in Robotics and Mechatronics Engineering from (<a href="https://www.dgist.ac.kr/en/" target="_blank">DGIST</a>), South Korea in 2023, M.S. degree in Computer Science from Chonbuk National University, South Korea in 2018, and B.S. degree in Computer Science from Abdelhamid Mehri Constantine 2 University, Algeria in 2015.</p>

    <p>My research focuses on leveraging machine learning, including large language models (LLMs) and computer vision, to tackle challenges in cancer diagnosis and tumor characterization. Through my interdisciplinary expertise, I strive to push the boundaries of how machine learning and language-based approaches can transform cancer diagnostics and pave the way for novel research in personalized medicine and precision oncology.</p>

    <a href="https://scholar.google.com/citations?user=8jHbkMcAAAAJ" target="_blank">Google Scholar Profile</a>
</div>

<div class="section highlights">
    <h2 class="gradient-text">Research Highlights</h2>
    <div class="highlight-grid">
        <div class="highlight-card">
            <h3>Medical Image Analysis</h3>
            <p>Developing advanced algorithms for medical image processing, segmentation, and classification.</p>
        </div>
        <div class="highlight-card">
            <h3>Few-Shot Learning</h3>
            <p>Innovation in learning from limited data samples through novel neural network architectures.</p>
        </div>
        <div class="highlight-card">
            <h3>Visual-Language Representation</h3>
            <p>Exploring the intersection of vision and language for medical image analysis.</p>
        </div>
    </div>
</div>

<div class="section news">
    <h2 class="gradient-text">Latest News</h2>
    {% for post in site.posts limit:3 %}
    <div class="news-item">
        <span class="news-date">{{ post.date | date: "%B %d, %Y" }}</span>
        <h4>{{ post.title }}</h4>
          {% if post.description %}
            <p>{{ post.description}}</p>
          {% endif %}
    </div>
    {% endfor %}
</div>