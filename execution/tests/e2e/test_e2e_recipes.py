import pytest
from playwright.sync_api import Page, expect

def login_as_test_user(page: Page):
    page.goto(page.base_url + "/")
    page.locator("#gate-signup").click()
    page.locator('[name="display_name"]').fill("Test Chef")
    page.locator('[name="email"]').fill("recipes@e2e.com")
    page.locator("#gate-register button").click()
    # Wait for the network requests to finish and the UI to update
    expect(page.locator("#user-greeting")).to_be_visible()

def test_recipe_crud(page: Page):
    """Test full CRUD cycle for a recipe from UI."""
    login_as_test_user(page)
    page.goto(page.base_url + "/recipes.html")
    
    # CREATE
    page.locator("#btn-create-recipe").click()
    page.locator("#recipe-name").fill("CRUD Test Recipe")
    tag = page.locator("#new-tag-input")
    tag.fill("Weeknight meals")
    tag.press("Enter")
    expect(page.get_by_role("button", name="Remove tag Weeknight meals")).to_be_visible()
    tools = page.get_by_role("region", name="Equipment")
    tools.get_by_role("button", name="Add tool").click()
    tools.get_by_role("textbox", name="Tool name").fill("Chef knife")
    tools.get_by_role("button", name="Add tool").click()
    tools.get_by_role("textbox", name="Tool name").last.fill("Kitchen scale")
    page.locator("#btn-save-recipe").click()
    expect(page.locator("#toast")).to_contain_text("Recipe created!", timeout=5000)
    
    cards = page.locator(".recipe-card")
    expect(cards).to_have_count(1)
    expect(cards.first.locator("h3")).to_have_text("CRUD Test Recipe")
    
    # EDIT
    cards.first.locator("text='✏️ Edit'").click()
    expect(tools.get_by_role("textbox", name="Tool name").first).to_have_value("Chef knife")
    tools.get_by_role("button", name="Remove tool").first.click()
    page.get_by_role("button", name="Remove tag Weeknight meals").click()
    tag.fill("night")
    page.locator("#tag-suggestions").get_by_role("button", name="Weeknight meals").click()
    expect(page.get_by_role("button", name="Remove tag Weeknight meals")).to_be_visible()
    page.locator('.step-desc').fill('Bake the crust')
    page.locator('#btn-add-step').click()
    page.locator('.step-desc').last.fill('Mix the dough')
    page.locator('#reorder-steps').click()
    order = page.locator('#recipe-order')
    expect(order.get_by_role('combobox')).to_have_count(0)
    order.get_by_role('button', name='Move up Mix the dough').click()
    order.get_by_label('Group name', exact=True).fill('Base')
    order.get_by_role('button', name='Add group').click()
    order.get_by_label('Group name · Mix the dough').select_option('Base')
    order.get_by_role('button', name='Done').click()
    expect(page.locator('#steps-list .editor-group')).to_have_text('Base')
    page.locator("#recipe-name").fill("CRUD Updated Recipe")
    page.locator("#btn-save-recipe").click()
    expect(page.locator("#toast")).to_contain_text("Recipe updated!")
    expect(cards.first.locator("h3")).to_have_text("CRUD Updated Recipe")
    cards.first.get_by_text('✏️ Edit').click()
    expect(tools.get_by_role("textbox", name="Tool name")).to_have_value("Kitchen scale")
    expect(page.locator('.step-desc').first).to_have_value('Mix the dough')
    expect(page.locator('#steps-list .editor-group')).to_have_text('Base')
    page.locator('#btn-close-modal').click()
    
    # SEARCH
    search = page.locator("#recipe-search")
    card_node = cards.first.element_handle()
    search.fill("Not Found")
    expect(cards.first).to_be_hidden()
    search.fill("Updated")
    expect(cards.first).to_be_visible()
    assert card_node.evaluate("node => node === document.querySelector('.recipe-card')")
    
    # DELETE
    cards.first.locator("text='🗑️ Delete'").click()
    expect(page.locator("#delete-modal")).to_be_visible()
    page.locator("#btn-confirm-delete").click()
    
    expect(page.locator("#toast")).to_contain_text("Recipe deleted")
    expect(cards).to_have_count(0)


def test_account_settings_uses_kitchen_navigation(page):
    login_as_test_user(page)
    page.goto(page.base_url + "/auth/account")
    nav = page.get_by_role("navigation")
    menu = nav.get_by_role("button", name="Toggle menu")
    if menu.is_visible():
        menu.click()
    expect(nav.get_by_role("link", name="Manage Recipes")).to_be_visible()
    if menu.is_visible():
        menu.click()
    page.get_by_role("link", name="Back to your kitchen").click()
    expect(page).to_have_url(page.base_url + "/kitchen.html")


def test_recipe_share_link_preview_and_revoke(page):
    login_as_test_user(page)
    result = page.evaluate("""async () => {
      const headers={'Content-Type':'application/json',Authorization:'Bearer '+localStorage.getItem('wswe_token')};
      const recipe=await (await fetch('/recipes',{method:'POST',headers,body:JSON.stringify({name:'Shared soup',ingredients:[{name:'Onion',quantity:2,unit:'pieces',group_name:'Base'}],instruction_steps:[{step_number:1,description:'Chop {{Base::Onion|50%}}'},{step_number:2,description:'Add {{Base::Onion|50%}} to the stock'}]})})).json();
      const share=await (await fetch('/recipe-shares',{method:'POST',headers,body:JSON.stringify({recipe_id:recipe.id})})).json();
      return share;
    }""")
    page.goto(result['url'])
    expect(page.get_by_role('heading', name='Shared soup')).to_be_visible()
    assert '#' not in page.url
    page.get_by_role('button', name='Cook now').click()
    badges = page.get_by_role('button', name='1 pieces Onion')
    badge = badges.first
    ingredient = page.get_by_role('checkbox', name='2 pieces Onion')
    badge.click()
    expect(ingredient).not_to_be_checked()
    expect(badges.last).to_have_attribute('aria-pressed', 'false')
    ingredient.check()
    expect(ingredient).to_be_checked()
    ingredient.uncheck()
    expect(badge).to_have_attribute('aria-pressed', 'true')
    badge.click()
    expect(badge).to_have_attribute('aria-pressed', 'false')
    badge.click()
    page.get_by_role('checkbox', name='Chop 1 pieces Onion').check()
    page.reload()
    expect(page.get_by_role('checkbox', name='2 pieces Onion')).not_to_be_checked()
    expect(page.get_by_role('checkbox', name='Chop 1 pieces Onion')).to_be_checked()
    expect(badge).to_have_attribute('aria-pressed', 'true')
    assert result['url'].split('#')[-1] not in page.evaluate("localStorage.getItem('onionary.shared-cooking')")
    page.evaluate("""async id => {await fetch('/recipe-shares/'+id,{method:'DELETE',headers:{Authorization:'Bearer '+localStorage.getItem('wswe_token')}})}""",result['id'])
    page.goto(result['url'])
    expect(page.locator('#error')).to_contain_text('expired')


def test_dark_import_and_share_layout(page: Page):
    login_as_test_user(page)
    page.evaluate("localStorage.setItem('app_appearance','dark')")
    page.goto(page.base_url + '/recipes.html')
    page.locator('#btn-create-recipe').click()
    page.locator('#recipe-name').fill('Long recipe name for responsive layout')
    servings = page.locator('#recipe-servings')
    assert servings.evaluate('(el) => getComputedStyle(el).borderRadius === getComputedStyle(document.querySelector("#recipe-name")).borderRadius')
    assert servings.evaluate('(el) => el.getBoundingClientRect().height >= 40')
    expect(page.locator('a[href="/auth/account"]')).to_have_attribute('aria-label', 'Account settings')
    expect(page.locator('a[href="/auth/account"] svg')).to_have_count(1)
    servings.fill('4.32')
    page.locator('#btn-save-recipe').click()
    expect(page.locator('.recipe-card')).to_have_count(1)
    assert page.locator('#toast').evaluate('(el) => getComputedStyle(el).color !== getComputedStyle(el).backgroundColor')
    card = page.locator('.recipe-card').first
    assert card.evaluate('(el) => el.scrollWidth <= el.clientWidth + 1')
    card.get_by_text('Share recipe copy').click()
    dialog = page.locator('dialog[open]')
    expect(dialog).to_be_visible()
    box = dialog.bounding_box()
    width = page.evaluate('innerWidth')
    assert abs(box['x'] + box['width']/2 - width/2) < 2
    assert box['y'] >= 0
    expect(dialog).to_have_css('opacity', '1')
    page.screenshot(path='.tmp/onionary-polish-web-share.png', full_page=True)
    dialog.get_by_text('Done', exact=True).click()
    card.get_by_text('✏️ Edit').click()
    expect(page.locator('#recipe-servings')).to_have_value('4.32')
    page.locator('#ingredients-list .ing-name').fill('Onion')
    page.locator('#recipe-icon').fill('🧅')
    assert page.locator('#edit-modal .modal-body').evaluate('(el) => el.scrollWidth <= el.clientWidth + 1')
    page.locator('#btn-save-recipe').click()
    expect(card.locator('h3')).to_contain_text('🧅')
    card.get_by_text('✏️ Edit').click()
    expect(page.locator('#recipe-icon')).to_have_value('🧅')

    page.locator('#btn-close-modal').click()
    page.locator('#btn-create-recipe').click()
    page.locator('#btn-mode-import').click()
    panel = page.locator('#import-panel')
    expect(panel).to_be_visible()
    expect(panel).to_have_css('background-color', 'rgb(43, 36, 42)')
    page.screenshot(path='.tmp/onionary-polish-web-import.png', full_page=True)


def test_deployed_backend_version_visible(page: Page):
    login_as_test_user(page)
    page.goto(page.base_url + '/recipes.html')
    version = page.request.get(page.base_url + '/version').json()['version']
    expect(page.locator('#deployed-version')).to_have_text('Onionary · ' + version)
