from bs4 import BeautifulSoup

def test_poster_filtering_logic():
    """Vérifie que la logique de filtrage retient bien les affiches et ignore le reste."""
    sample_html = """
    <div class="catalog-list-item">
        <h3>Affiche du film DUNE</h3>
        <p>En salles le 28 février</p>
        <span class="points">250 points</span>
    </div>
    <div class="catalog-list-item">
        <h3>Popcorn Moyen</h3>
        <span class="points">100 points</span>
    </div>
    <div class="catalog-list-item">
        <h3>Poster collector SPIDER-MAN</h3>
        <div class="disabled">Victime de son succès</div>
    </div>
    """
    
    soup = BeautifulSoup(sample_html, "html.parser")
    items = soup.find_all("div", class_="catalog-list-item")
    
    KEYWORDS_POSTERS = ["affiche", "poster"]
    detected_posters = []

    for item in items:
        title_tag = item.find("h3")
        title = title_tag.text.strip() if title_tag else ""
        if title and any(kw in title.lower() for kw in KEYWORDS_POSTERS):
            detected_posters.append(title)

    # Vérifications
    assert len(detected_posters) == 2
    assert "Affiche du film DUNE" in detected_posters
    assert "Poster collector SPIDER-MAN" in detected_posters
    assert "Popcorn Moyen" not in detected_posters