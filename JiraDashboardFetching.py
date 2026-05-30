import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

JIRA_URL = "https://jirard.intra.infineon.com/secure/Dashboard.jspa?openinstance"

# Output
OUT_DIR = r"C:\Users\Vislavath\Downloads\Jira_fetch"
OUT_FILE = os.path.join(OUT_DIR, "jira_grid.xlsx")
os.makedirs(OUT_DIR, exist_ok=True)

def switch_into_frame_with_grid(driver, wait, timeout=30):
    """
    Switch into the iframe that contains esu-filter-results-grid (if any).
    Returns True if switched; otherwise leaves default content and returns False.
    """
    driver.switch_to.default_content()

    # Try gadget-specific iframe first (if gadget id is known)
    try:
        iframe = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#gadget-208004 iframe, #gadget-208004 .dashboard-item-frame, #gadget-208004 iframe.flex-dashboard-item-frame")
        ))
        driver.switch_to.frame(iframe)
        # Verify presence using JS
        found = driver.execute_script("""
            try{
                const findDeep=(root,sel)=>{
                    const res=[];const vis=(n)=>{
                        if(!n) return;
                        try{ n.querySelectorAll && n.querySelectorAll(sel).forEach(e=>res.push(e)); }catch(e){}
                        if(n.shadowRoot) vis(n.shadowRoot);
                        (n.children?Array.from(n.children):[]).forEach(vis);
                    };
                    vis(root||document); return res;
                };
                return !!(findDeep(document,'esu-filter-results-grid')[0]);
            }catch(e){ return false; }
        """)
        if found: 
            return True
        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()

    # Fallback: iterate through all iframes
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for idx, f in enumerate(frames):
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(f)
            found = driver.execute_script("""
                try{
                    const findDeep=(root,sel)=>{
                        const res=[];const vis=(n)=>{
                            if(!n) return;
                            try{ n.querySelectorAll && n.querySelectorAll(sel).forEach(e=>res.push(e)); }catch(e){}
                            if(n.shadowRoot) vis(n.shadowRoot);
                            (n.children?Array.from(n.children):[]).forEach(vis);
                        };
                        vis(root||document); return res;
                    };
                    return !!(findDeep(document,'esu-filter-results-grid')[0]);
                }catch(e){ return false; }
            """)
            if found:
                return True
        except Exception:
            pass

    # Not found in any frame; remain in default content
    driver.switch_to.default_content()
    return False

def scrape_ag_grid(driver):
    """
    Returns a dict: {'headers': [...], 'rows': [[...], ...], 'error': str|None, 'method': 'api'|'dom'|None}
    Guaranteed to return a dict (never None).
    """
    js = r"""
    try{
        const findDeep=(root,sel)=>{
            const res=[];
            const vis=(n)=>{
                if(!n) return;
                try{ n.querySelectorAll && n.querySelectorAll(sel).forEach(e=>res.push(e)); }catch(e){}
                if(n.shadowRoot) vis(n.shadowRoot);
                (n.children?Array.from(n.children):[]).forEach(vis);
            };
            vis(root||document);
            return res;
        };

        let comp = findDeep(document, 'esu-filter-results-grid')[0] || null;
        if(!comp){
            return {headers:[], rows:[], error:'esu-filter-results-grid not found', method:null};
        }

        const root = comp.shadowRoot ? comp.shadowRoot : comp;

        // Try ag-Grid API first (fast & robust if exposed)
        try{
            const api = comp.gridApi || comp.api || comp.__agApi || (comp.gridOptions && comp.gridOptions.api) || null;
            const columnApi = comp.columnApi || (comp.gridOptions && comp.gridOptions.columnApi) || null;

            if(api && api.getDisplayedRowCount){
                let headers = [];
                if(columnApi && columnApi.getAllGridColumns){
                    headers = columnApi.getAllGridColumns().map(c => (c.getColDef().headerName || c.getColDef().field || c.getColId() || '').toString().trim());
                } else {
                    const hEls = root.querySelectorAll('.ag-header-cell-text');
                    headers = Array.from(hEls).map(e => (e.textContent||'').trim());
                }

                const rows = [];
                const count = api.getDisplayedRowCount();
                const colDefs = api.getColumnDefs ? api.getColumnDefs() : null;
                const fields = colDefs ? colDefs.map(c => c.field || c.colId || c.headerName) : null;

                for(let i=0;i<count;i++){
                    const rowNode = api.getDisplayedRowAtIndex(i);
                    const data = rowNode && rowNode.data ? rowNode.data : null;
                    if(data){
                        if(fields){
                            rows.push(fields.map(f => data && (data[f]!==undefined && data[f]!==null) ? String(data[f]) : ''));
                        }else{
                            // Best-effort order from data
                            rows.push(Object.values(data).map(v => v===null||v===undefined?'':String(v)));
                        }
                    }
                }

                return {headers:headers, rows:rows, error:null, method:'api'};
            }
        }catch(e){
            // fall through to DOM path
        }

        // Fallback: DOM header + virtual scroll row harvesting
        const headerEls = root.querySelectorAll('.ag-header-cell-text');
        const headers = Array.from(headerEls).map(e => (e.textContent || '').trim());

        const viewport = root.querySelector('.ag-center-cols-viewport, .ag-body-viewport');
        const container = root.querySelector('.ag-center-cols-container, .ag-center-cols-clipper, .ag-body-viewport .ag-center-cols-container');

        if(!viewport || !container){
            return {headers:headers, rows:[], error:'ag-Grid viewport/container not found', method:'dom'};
        }

        // Scroll & collect visible rows
        const map = new Map();
        const collect = () => {
            const rows = container.querySelectorAll('.ag-row');
            rows.forEach(r => {
                const idx = r.getAttribute('row-index') || r.getAttribute('aria-rowindex') || r.style.top || String(map.size);
                const cells = Array.from(r.querySelectorAll('.ag-cell')).map(c => (c.innerText||'').replace(/\s+/g,' ').trim());
                if(cells.length) map.set(idx, cells);
            });
        };

        viewport.scrollTop = 0;
        collect();
        let guard = 0, prevTop = -1;
        const maxLoop = 2000;
        while(viewport.scrollTop !== prevTop && guard < maxLoop){
            prevTop = viewport.scrollTop;
            viewport.scrollTop = Math.min(viewport.scrollTop + 800, (viewport.scrollHeight || (container.scrollHeight||0)));
            collect();
            guard++;
        }

        const rows = Array.from(map.entries())
                          .sort((a,b)=> (parseFloat(a[0])||0) - (parseFloat(b[0])||0))
                          .map(e => e[1]);

        return {headers:headers, rows:rows, error:null, method:'dom'};
    }catch(err){
        return {headers:[], rows:[], error: String(err && (err.stack||err)), method:null};
    }
    """
    try:
        result = driver.execute_script(js)
        # Ensure a dict-like result is always returned
        if not isinstance(result, dict):
            return {'headers': [], 'rows': [], 'error': 'JS returned non-dict/None', 'method': None}
        return result
    except Exception as e:
        return {'headers': [], 'rows': [], 'error': f'execute_script failed: {e}', 'method': None}

def run():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 40)
    try:
        driver.get(JIRA_URL)

        # Give Jira time to load dashboard and gadgets
        time.sleep(5)

        # Try to switch into the correct iframe (if any)
        switched = switch_into_frame_with_grid(driver, wait)
        if not switched:
            # Some gadgets are not in iframes; continue in default content
            driver.switch_to.default_content()

        # Try scraping
        result = scrape_ag_grid(driver)

        if result.get('error'):
            print("[Error] Grid scrape:", result['error'])
            print("Hints:")
            print("  • Ensure you're logged in to Jira (SSO).")
            print("  • The gadget might be in a different iframe (id changed).")
            print("  • The custom element may use a closed shadowRoot (limits DOM scraping).")
            return

        headers = result.get('headers', [])
        rows = result.get('rows', [])
        method = result.get('method')

        if not rows:
            print("[Warn] No rows found. The grid may be empty or not visible yet.")
            return

        # Normalize rows length to headers
        if headers:
            norm = []
            for r in rows:
                if len(r) < len(headers):
                    r = r + [''] * (len(headers) - len(r))
                elif len(r) > len(headers):
                    r = r[:len(headers)]
                norm.append(r)
            df = pd.DataFrame(norm, columns=headers)
        else:
            df = pd.DataFrame(rows)

        df.to_excel(OUT_FILE, index=False)  # pandas will use openpyxl
        print(f"[Success] Extracted {len(df)} rows using method={method}. Saved to: {OUT_FILE}")

    except WebDriverException as e:
        print("[Fatal] WebDriver exception:", e)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    run()