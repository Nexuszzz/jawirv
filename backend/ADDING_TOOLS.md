# JAWIR OS - Guide: Adding New Tools

## Step-by-Step: Menambahkan Tool Baru ke Function Calling

### Step 1: Define Input Schema

Tambahkan Pydantic `BaseModel` di `agent/tools_registry.py`:

```python
class MyNewToolInput(BaseModel):
    """Input schema for my new tool."""
    param1: str = Field(description="Deskripsi parameter dalam bahasa natural")
    param2: int = Field(default=10, description="Opsional dengan default value")
```

**Rules:**
- Deskripsi `Field()` harus jelas — Gemini membaca ini untuk memutuskan parameter
- Gunakan tipe sederhana: `str`, `int`, `float`, `bool`, `list[str]`
- Optional params harus punya `default=...`

### Step 2: Create Tool Factory Function

```python
def create_my_new_tool() -> StructuredTool:
    """Create my new tool."""

    async def _my_tool(param1: str, param2: int = 10) -> str:
        """Short description for logging."""
        try:
            # Your tool logic here
            result = do_something(param1, param2)
            return f"✅ Success: {result}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    return StructuredTool.from_function(
        func=_my_tool,
        coroutine=_my_tool,  # WAJIB: harus async
        name="my_new_tool",   # Unique name, lowercase, underscore
        description=(
            "Deskripsi natural language tentang kapan tool ini digunakan. "
            "Gemini akan membaca ini untuk memutuskan apakah perlu memanggil tool. "
            "Sertakan contoh use case."
        ),
        args_schema=MyNewToolInput,
    )
```

**Rules:**
- `name` harus unique (tidak boleh duplikat)
- `coroutine` WAJIB diisi (LangGraph butuh async)
- `description` harus natural language, bukan teknis
- Return `str` selalu (bukan dict/object)
- Handle error dengan try-catch, return error message

### Step 3: Register in `get_all_tools()`

```python
def get_all_tools() -> list[StructuredTool]:
    tools = []
    
    # ... existing tools ...
    
    # N. My New Tool
    try:
        tools.append(create_my_new_tool())
        logger.info("✅ Registered: my_new_tool")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register my_new_tool: {e}")
    
    return tools
```

### Step 4: Update System Prompt (if needed)

Jika tool baru perlu instruksi khusus, tambahkan ke `FUNCTION_CALLING_SYSTEM_PROMPT`
di `agent/function_calling_executor.py`:

```python
FUNCTION_CALLING_SYSTEM_PROMPT = """...
- my_new_tool: Untuk [deskripsi kapan digunakan]
...
"""
```

### Step 5: Add Tests

Tambahkan test di `tests/test_tools_registry.py`:

```python
def test_create_my_new_tool(self):
    from agent.tools_registry import create_my_new_tool
    tool = create_my_new_tool()
    assert tool.name == "my_new_tool"
```

Update expected tool count:
```python
def test_returns_N_tools(self):
    tools = get_all_tools()
    assert len(tools) == 13  # Was 12, now 13
```

### Step 6: Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

All tests harus pass sebelum commit.

## Checklist

- [ ] Input schema (Pydantic BaseModel) dengan Field descriptions
- [ ] Factory function (`create_xxx_tool()`) dengan async coroutine
- [ ] Registered di `get_all_tools()`
- [ ] System prompt updated (jika perlu)
- [ ] Test ditambahkan dan pass
- [ ] Tool count di test di-update
- [ ] Expected tools list di test di-update
