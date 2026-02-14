import pytest
from src.wiki_client import WikiFrequencyCounter


class TestLinkExtraction:
    """Test link extraction from HTML content using real Wikipedia HTML."""
    
    def test_extract_links_from_gyorzamoly(self, gyorzamoly_html):
        """Test link extraction from real Hungarian Wikipedia article."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)
        links = wiki.extract_links_from_html(gyorzamoly_html)
        
        # Verify we got links
        assert len(links) > 0
        
        # Verify specific expected links are present
        assert "Község" in links
        assert "Magyarország" in links
        assert "Győr" in links
        assert "Szigetköz" in links
    
    def test_extract_links_from_msci(self, msci_html):
        """Test link extraction from real English Wikipedia article."""
        wiki = WikiFrequencyCounter("MSCI", 1)
        links = wiki.extract_links_from_html(msci_html)
        
        # Verify we got links
        assert len(links) > 0
        
        # Verify specific expected links
        assert "New_York_City" in links
        assert "Morgan_Stanley" in links
        assert "MSCI_World" in links
    
    def test_extract_links_filters_special_pages(self, gyorzamoly_html):
        """Verify that special pages are filtered from real HTML."""
        wiki = WikiFrequencyCounter("Test", 1)
        links = wiki.extract_links_from_html(gyorzamoly_html)
        
        # Should not contain any special pages
        special_prefixes = ["File:", "Special:", "Help:", "Category:", 
                           "Template:", "Wikipédia:", "Wikipedia:"]
        
        for link in links:
            for prefix in special_prefixes:
                assert not link.startswith(prefix), \
                    f"Found special page link: {link}"
    
    def test_extract_links_no_duplicates(self, gyorzamoly_html):
        """Test that duplicate links are removed."""
        wiki = WikiFrequencyCounter("Test", 1)
        links = wiki.extract_links_from_html(gyorzamoly_html)
        
        # All links should be unique
        assert len(links) == len(set(links))
    
    def test_extract_links_empty_content(self):
        """Test extraction from content with no links."""
        wiki = WikiFrequencyCounter("Test", 1)
        html = """
        <div id="mw-content-text">
            <p>Text with no links</p>
        </div>
        """
        links = wiki.extract_links_from_html(html)
        
        assert len(links) == 0
    
    def test_extract_links_no_content_div(self):
        """Test extraction when mw-content-text div is missing."""
        wiki = WikiFrequencyCounter("Test", 1)
        html = "<html><body><p>Some text</p></body></html>"
        links = wiki.extract_links_from_html(html)
        
        assert len(links) == 0
    
    def test_extract_links_excludes_navbox_links(self):
        """Test that links from navbox elements are excluded."""
        wiki = WikiFrequencyCounter("Győrzámoly", 1)
        html = """
        <div id="mw-content-text">
            <p>Main article content with <a href="/wiki/Győr">Győr</a> link.</p>
            <div class="navbox">
                <a href="/wiki/Csapod">Csapod</a>
                <a href="/wiki/Szerecseny">Szerecseny</a>
                <a href="/wiki/Csér">Csér</a>
            </div>
            <table class="infobox">
                <a href="/wiki/InfoboxLink">InfoboxLink</a>
            </table>
        </div>
        """
        links = wiki.extract_links_from_html(html)
        
        # Main content link should be present
        assert "Győr" in links
        
        # Navbox links should NOT be present
        assert "Csapod" not in links
        assert "Szerecseny" not in links
        assert "Csér" not in links
        
        # Infobox links should NOT be present
        assert "InfoboxLink" not in links
