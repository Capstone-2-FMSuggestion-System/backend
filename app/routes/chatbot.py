# from fastapi import APIRouter, Depends, Body
# from typing import Dict
# import json
# from ..utils.ai_models import load_models
# from ..database import get_db
# from sqlalchemy.orm import Session
# from ..cache import get_cache, set_cache

# router = APIRouter(prefix="/api", tags=["chatbot"])

# # Load AI models
# classifier, tokenizer, model, labels = load_models()

# # Prompt for mT5
# prompt = (
#     "Bạn là một chuyên gia dinh dưỡng thân thiện. Nhiệm vụ của bạn là tư vấn cho người dùng về các vấn đề liên quan đến dinh dưỡng. "
#     "Chỉ trả lời các câu hỏi thuộc lĩnh vực dinh dưỡng. Nếu câu hỏi không liên quan đến dinh dưỡng, "
#     "hãy trả lời: 'Xin lỗi, tôi chỉ có thể trả lời các câu hỏi về dinh dưỡng.' "
#     "Nếu người dùng chào hỏi (ví dụ: 'hello', 'xin chào'), hãy trả lời: 'Xin chào! Tôi là chatbot tư vấn dinh dưỡng. Bạn muốn hỏi gì về dinh dưỡng nào?'"
# )

# def classify_question(question):
#     """
#     Phân loại xem câu hỏi có liên quan đến dinh dưỡng hay không bằng cách sử dụng XLM-RoBERTa.
#     Trả về toàn bộ kết quả để xử lý nhiều nhãn
#     """
#     result = classifier(question, labels)
#     return result  # Trả về toàn bộ kết quả để xử lý nhiều nhãn

# def generate_answer(question: str) -> str:
#     """
#     Tạo câu trả lời cho câu hỏi về dinh dưỡng sử dụng mT5.
#     """
#     input_text = f"{prompt}\nUser: {question}\nAssistant:"
#     inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
#     outputs = model.generate(
#         inputs["input_ids"],
#         max_length=200,
#         num_beams=5,
#         early_stopping=True
#     )
#     answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
#     return answer[len(input_text):].strip()

# @router.post("/chatbot")
# async def chatbot_endpoint(question: str = Body(..., embed=True), db: Session = Depends(get_db)):
#     """
#     Endpoint API Chatbot nhận một câu hỏi và trả về câu trả lời.
#     Xử lý các loại câu hỏi dựa trên phân loại và điểm tin cậy.
#     """
#     # Check cache first
#     cache_key = f"chatbot:{question}"
#     cached_response = await get_cache(cache_key)
    
#     if cached_response:
#         return json.loads(cached_response)
    
#     # Process the question
#     classification = classify_question(question)
#     top_label = classification['labels'][0]
#     score = classification['scores'][0]
    
#     if top_label == "dinh dưỡng" and score > 0.6:
#         response = generate_answer(question)
        
#         # Log the interaction to database
#         db.execute(
#             "INSERT INTO chatbot_logs (question, answer, created_at) VALUES (:q, :a, NOW())", 
#             {"q": question, "a": response}
#         )
#         db.commit()
        
#         # Cache the response
#         result = {"response": response}
#         await set_cache(cache_key, json.dumps(result), 3600)  # Cache for 1 hour
        
#         return result
#     elif top_label == "chào hỏi" and score > 0.6:
#         response = "Xin chào! Tôi là chatbot tư vấn dinh dưỡng. Bạn muốn hỏi gì về dinh dưỡng nào?"
        
#         # Cache the response
#         result = {"response": response}
#         await set_cache(cache_key, json.dumps(result), 3600)  # Cache for 1 hour
        
#         return result
#     else:
#         response = "Xin lỗi, tôi chỉ có thể trả lời các câu hỏi về dinh dưỡng."
        
#         # Cache the response
#         result = {"response": response}
#         await set_cache(cache_key, json.dumps(result), 3600)  # Cache for 1 hour
        
#         return result