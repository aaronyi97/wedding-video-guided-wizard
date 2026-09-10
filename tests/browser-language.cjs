const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_BIN?{executablePath:process.env.BROWSER_BIN}:{})});
 try {
 const context=await browser.newContext({viewport:{width:390,height:844}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto((process.env.CARD_URL||'http://127.0.0.1:8734/')+'?lang=en');
 assert.equal(await page.locator('html').getAttribute('lang'),'en');
 const untranslated=await page.evaluate(()=>{const body=document.body.cloneNode(true);body.querySelectorAll('script,style,#langToggle').forEach(x=>x.remove());return (body.textContent.match(/[\u3400-\u9fff]+/g)||[]);});
 assert.deepEqual(untranslated,[],'Untranslated English UI');
 const placeholders=await page.locator('[placeholder],[aria-label]').evaluateAll(els=>els.flatMap(el=>['placeholder','aria-label'].map(a=>el.getAttribute(a)||'')));
 assert.ok(placeholders.every(s=>!/[\u3400-\u9fff]/.test(s)),JSON.stringify(placeholders));
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async t=>window.copied=t},configurable:true}));
 await page.click('#btnCopy');assert.equal(await page.evaluate(()=>window.copied),undefined);
 assert.ok((await page.locator('#toast').innerText()).startsWith('Please complete:'));
 for(const [id,value] of Object.entries({groom:'Alex',bride:'Emma',a1_fill:'We met through friends in autumn.',a1_extra:'A blue notebook',a2_fill:'We cooked dinner together.',a3_fill:'No proposal; we decided together.',a4_fill:'Sunday walks.',a5_fill:'I am right beside you.',notes:'Natural English narration.',add_thing_t:'Our first concert ticket',avoid:'No fictional scenes',swap:'None'}))await page.locator('#'+id).fill(value);
 for(const id of ['occasion_0','style_1','styleMode_0','a1_pick_2','a2_pick_6','a3_pick_x','a4_pick_x','a5_venue_x','a5_pick_2','music_own'])await page.locator('#'+id).check({force:true});
 for(const [id,value] of Object.entries({a3_pick_other:'No formal proposal',a4_pick_other:'Walking together',a5_venue_other:'Not decided yet',music_own_t:'An instrumental piano track'}))await page.locator('#'+id).fill(value);
 await page.click('#btnCopy');const copied=await page.evaluate(()=>window.copied);
 assert.ok(copied.includes('Act 1 Meeting'));assert.ok(copied.includes('No formal proposal'));assert.ok(copied.includes('Our first concert ticket'));assert.ok(copied.includes('Missing：None; ready to copy'));
 assert.ok(!/[\u3400-\u9fff]/.test(copied),copied);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 if(process.env.SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'intake-en-mobile.png'),fullPage:true});
 await page.click('#langToggle');await page.waitForURL('**lang=zh');
 assert.equal(await page.locator('#groom').inputValue(),'Alex');assert.ok(await page.locator('#a3_pick_x').isChecked());
 assert.equal(await page.locator('#a3_pick_other').inputValue(),'No formal proposal');
 assert.equal(await page.locator('h1').innerText(),'婚礼故事采集卡');
 await page.click('#langToggle');await page.waitForURL('**lang=en');
 await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw new Error('blocked')}},configurable:true}));
 await page.click('#btnCopy');assert.equal(await page.locator('#copyFallback').inputValue(),copied);assert.ok(await page.locator('#copyFallback').isVisible());
 await page.setViewportSize({width:1280,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 if(process.env.SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.SCREENSHOT_DIR,'intake-en-desktop.png'),fullPage:true});
 assert.deepEqual(errors,[]);console.log(JSON.stringify({passed:true,checks:['English labels and placeholders','English missing-field feedback','full English copied card','no Chinese leakage','language switch preserves typed answers and selected options','clipboard fallback','mobile and desktop layout','no JS errors']}));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
