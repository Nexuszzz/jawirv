"""
Manual test untuk forms_add_question - debug timeout issue
"""
import asyncio
import sys
import time

sys.path.insert(0, "D:\\expo\\jawirv3\\jawirv2\\jawirv2\\backend")

async def test_forms_add_question():
    """Test forms_add_question dengan berbagai tipe pertanyaan"""
    from tools.google_workspace import GoogleWorkspaceMCP
    
    gws = GoogleWorkspaceMCP()
    
    # Form ID dari stress test
    form_id = "1Pc10m0eujWBxCxx978CJC9aYO-URujxJv8yOiUR9vog"
    
    print("=" * 60)
    print("TEST 1: Text Question (Jawaban Singkat)")
    print("=" * 60)
    start = time.time()
    
    try:
        request = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": "Nama Anda?",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "textQuestion": {"paragraph": False}
                            }
                        }
                    },
                    "location": {"index": 0}
                }
            }]
        }
        
        result = gws.batch_update_form(form_id=form_id, requests=request["requests"])
        elapsed = time.time() - start
        
        print(f"✅ SUCCESS ({elapsed:.1f}s)")
        print(f"Result: {result.get('output', result)[:200]}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ FAILED ({elapsed:.1f}s): {e}")
    
    print()
    
    # Test 2: Multiple Choice
    print("=" * 60)
    print("TEST 2: Multiple Choice (Rating 1-5)")
    print("=" * 60)
    start = time.time()
    
    try:
        request = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": "Berapa rating Anda untuk layanan ini? (1-5)",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [
                                        {"value": "1 - Sangat Buruk"},
                                        {"value": "2 - Buruk"},
                                        {"value": "3 - Cukup"},
                                        {"value": "4 - Baik"},
                                        {"value": "5 - Sangat Baik"}
                                    ]
                                }
                            }
                        }
                    },
                    "location": {"index": 0}
                }
            }]
        }
        
        result = gws.batch_update_form(form_id=form_id, requests=request["requests"])
        elapsed = time.time() - start
        
        print(f"✅ SUCCESS ({elapsed:.1f}s)")
        print(f"Result: {result.get('output', result)[:200]}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ FAILED ({elapsed:.1f}s): {e}")
    
    print()
    
    # Test 3: Paragraph (Jawaban Panjang)
    print("=" * 60)
    print("TEST 3: Paragraph (Jawaban Panjang)")
    print("=" * 60)
    start = time.time()
    
    try:
        request = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": "Saran dan masukan Anda?",
                        "questionItem": {
                            "question": {
                                "required": False,
                                "textQuestion": {"paragraph": True}
                            }
                        }
                    },
                    "location": {"index": 0}
                }
            }]
        }
        
        result = gws.batch_update_form(form_id=form_id, requests=request["requests"])
        elapsed = time.time() - start
        
        print(f"✅ SUCCESS ({elapsed:.1f}s)")
        print(f"Result: {result.get('output', result)[:200]}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ FAILED ({elapsed:.1f}s): {e}")
    
    print()
    
    # Test 4: Checkbox (Multiple Selection)
    print("=" * 60)
    print("TEST 4: Checkbox (Pilihan Ganda - Multi)")
    print("=" * 60)
    start = time.time()
    
    try:
        request = {
            "requests": [{
                "createItem": {
                    "item": {
                        "title": "Tool mana yang paling stabil? (pilih semua yang sesuai)",
                        "questionItem": {
                            "question": {
                                "required": False,
                                "choiceQuestion": {
                                    "type": "CHECKBOX",
                                    "options": [
                                        {"value": "Web Search"},
                                        {"value": "Python"},
                                        {"value": "Sheets"},
                                        {"value": "Docs"},
                                        {"value": "Drive"},
                                        {"value": "Forms"},
                                        {"value": "Calendar"},
                                        {"value": "Desktop"},
                                        {"value": "KiCad"}
                                    ]
                                }
                            }
                        }
                    },
                    "location": {"index": 0}
                }
            }]
        }
        
        result = gws.batch_update_form(form_id=form_id, requests=request["requests"])
        elapsed = time.time() - start
        
        print(f"✅ SUCCESS ({elapsed:.1f}s)")
        print(f"Result: {result.get('output', result)[:200]}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ FAILED ({elapsed:.1f}s): {e}")
    
    print()
    print("=" * 60)
    print("MANUAL TEST COMPLETED")
    print("=" * 60)
    print(f"\nForm URL: https://docs.google.com/forms/d/{form_id}/edit")


if __name__ == "__main__":
    asyncio.run(test_forms_add_question())
