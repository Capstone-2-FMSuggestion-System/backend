# from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
# import pickle
# import os

# def initialize_models():
#     """
#     Khởi tạo và lưu các mô hình AI cho chatbot dinh dưỡng.
#     - XLM-RoBERTa để phân loại zero-shot các câu hỏi dinh dưỡng
#     - mT5 để tạo câu trả lời bằng tiếng Việt
#     """
#     # Phân loại với XLM-RoBERTa
#     classifier = pipeline(
#         "zero-shot-classification",
#         model="xlm-roberta-base",
#         hypothesis_template="Câu này thuộc về chủ đề {}.",  # Cung cấp ngữ cảnh cho nhãn
#     )
#     labels = ["dinh dưỡng", "chào hỏi", "không liên quan"]

#     # Tạo câu trả lời với mT5
#     model_name = "google/mt5-base"
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

#     # Create directory if it doesn't exist
#     os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
#     
#     # Lưu mô hình để tái sử dụng
#     with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_models.pkl"), "wb") as f:
#         pickle.dump({"classifier": classifier, "tokenizer": tokenizer, "model": model, "labels": labels}, f)
#     
#     return classifier, tokenizer, model, labels

# def load_models():
#     """
#     Tải các mô hình AI đã được lưu trước đó cho chatbot dinh dưỡng.
#     Trả về classifier, tokenizer, model và labels.
#     """
#     model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai_models.pkl")
#     
#     if os.path.exists(model_path):
#         with open(model_path, "rb") as f:
#             models = pickle.load(f)
#         return models["classifier"], models["tokenizer"], models["model"], models["labels"]
#     else:
#         return initialize_models()