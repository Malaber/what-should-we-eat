import pytest
from playwright.sync_api import Page, expect

def login_as_test_user(page: Page):
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator("#registration summary").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("recipes@e2e.com")
    page.locator("#register button").click()
    # Wait for the network requests to finish and the UI to update
    expect(page.locator("#user-greeting")).to_be_visible()

def test_recipe_crud(page: Page):
    """Test full CRUD cycle for a recipe from UI."""
    login_as_test_user(page)
    page.goto(page.base_url + "/recipes.html")
    
    # CREATE
    page.locator("#btn-create-recipe").click()
    page.locator("#recipe-name").fill("CRUD Test Recipe")
    page.locator("#btn-save-recipe").click()
    expect(page.locator("#toast")).to_contain_text("Recipe created!", timeout=5000)
    
    cards = page.locator(".recipe-card")
    expect(cards).to_have_count(1)
    expect(cards.first.locator("h3")).to_have_text("CRUD Test Recipe")
    
    # EDIT
    cards.first.locator("text='✏️ Edit'").click()
    page.locator("#recipe-name").fill("CRUD Updated Recipe")
    page.locator("#btn-save-recipe").click()
    expect(page.locator("#toast")).to_contain_text("Recipe updated!")
    expect(cards.first.locator("h3")).to_have_text("CRUD Updated Recipe")
    
    # SEARCH
    search = page.locator("#recipe-search")
    search.fill("Not Found")
    expect(cards).to_have_count(0)
    search.fill("Updated")
    expect(cards).to_have_count(1)
    
    # DELETE
    cards.first.locator("text='🗑️ Delete'").click()
    expect(page.locator("#delete-modal")).to_be_visible()
    page.locator("#btn-confirm-delete").click()
    
    expect(page.locator("#toast")).to_contain_text("Recipe deleted")
    expect(cards).to_have_count(0)


def test_recipe_share_link_preview_and_revoke(page):
    login_as_test_user(page)
    result = page.evaluate("""async () => {
      const headers={'Content-Type':'application/json',Authorization:'Bearer '+localStorage.getItem('wswe_token')};
      const recipe=await (await fetch('/recipes',{method:'POST',headers,body:JSON.stringify({name:'Shared soup',ingredients:[{name:'Onion',quantity:2,unit:'pieces'}],instruction_steps:[{step_number:1,description:'Chop'}]})})).json();
      const share=await (await fetch('/recipe-shares',{method:'POST',headers,body:JSON.stringify({recipe_id:recipe.id})})).json();
      return share;
    }""")
    page.goto(result['url'])
    expect(page.get_by_role('heading', name='Shared soup')).to_be_visible()
    assert '#' not in page.url
    page.evaluate("""async id => {await fetch('/recipe-shares/'+id,{method:'DELETE',headers:{Authorization:'Bearer '+localStorage.getItem('wswe_token')}})}""",result['id'])
    page.goto(result['url'])
    expect(page.locator('#error')).to_contain_text('expired')
