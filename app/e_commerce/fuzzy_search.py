import re
from typing import List, Dict, Set

class FuzzySearchHelper:
    """Helper class for fuzzy search functionality"""
    
    def __init__(self):
        # Từ điển từ đồng nghĩa cho thực phẩm
        self.synonyms = {
            # Thịt
            'thit': ['thịt', 'meat'],
            'ga': ['gà', 'chicken', 'ga'],
            'bo': ['bò', 'beef', 'bo'],
            'heo': ['heo', 'pork', 'lợn', 'lon'],
            'ca': ['cá', 'fish', 'ca'],
            'tom': ['tôm', 'shrimp', 'tom'],
            'cua': ['cua', 'crab'],
            
            # Rau củ
            'rau': ['rau', 'vegetable', 'vegetables'],
            'cu': ['củ', 'root'],
            'cai': ['cải', 'cabbage', 'cai'],
            'carot': ['cà rót', 'carrot', 'carot'],
            'khoai': ['khoai', 'potato'],
            'hanh': ['hành', 'onion', 'hanh'],
            'toi': ['tỏi', 'garlic', 'toi'],
            
            # Trái cây
            'trai': ['trái', 'fruit'],
            'cay': ['cây', 'tree'],
            'cam': ['cam', 'orange'],
            'tao': ['táo', 'apple', 'tao'],
            'chuoi': ['chuối', 'banana', 'chuoi'],
            'xoai': ['xoài', 'mango', 'xoai'],
            'nho': ['nho', 'grape'],
            
            # Bánh kẹo
            'banh': ['bánh', 'cake', 'bread', 'banh'],
            'keo': ['kẹo', 'candy', 'keo'],
            'kem': ['kem', 'ice cream'],
            'sua': ['sữa', 'milk', 'sua'],
            
            # Gia vị
            'muoi': ['muối', 'salt', 'muoi'],
            'duong': ['đường', 'sugar', 'duong'],
            'dau': ['dầu', 'oil', 'dau'],
            'tuong': ['tương', 'sauce', 'tuong'],
            'nuoc': ['nước', 'water', 'nuoc'],
            
            # Đồ uống
            'tra': ['trà', 'tea', 'tra'],
            'cafe': ['cà phê', 'coffee', 'cafe'],
            'bia': ['bia', 'beer'],
            'ruou': ['rượu', 'wine', 'alcohol', 'ruou'],
            
            # Ngũ cốc
            'gao': ['gạo', 'rice', 'gao'],
            'mi': ['mì', 'noodle', 'mi'],
            'bun': ['bún', 'vermicelli', 'bun'],
            'pho': ['phở', 'pho'],
            'com': ['cơm', 'rice', 'com'],
            
            # Đậu hạt
            'dau': ['đậu', 'bean', 'dau'],
            'hat': ['hạt', 'seed', 'nut', 'hat'],
            'nhan': ['nhân', 'kernel', 'nhan'],
            
            # Từ khóa chung
            'tuoi': ['tươi', 'fresh', 'tuoi'],
            'kho': ['khô', 'dry', 'dried', 'kho'],
            'dong': ['đông', 'frozen', 'dong'],
            'huu': ['hữu', 'organic', 'huu'],
            'co': ['cơ', 'organic', 'co'],
        }
        
        # Từ điển sửa lỗi chính tả phổ biến
        self.spelling_corrections = {
            # Lỗi gõ phổ biến
            'gà': ['ga', 'gaa', 'gah'],
            'cá': ['ca', 'caa'],
            'bò': ['bo', 'boo'],
            'tôm': ['tom', 'tohm'],
            'bánh': ['banh', 'banhh'],
            'sữa': ['sua', 'suaa'],
            'trà': ['tra', 'traa'],
            'cà phê': ['cafe', 'ca phe', 'caphe'],
            'rau': ['rau', 'raau'],
            'thịt': ['thit', 'thiit'],
            'nước': ['nuoc', 'nuocc'],
            'đường': ['duong', 'duongg'],
            'muối': ['muoi', 'muoii'],
            'tỏi': ['toi', 'toii'],
            'hành': ['hanh', 'hanhh'],
            'cải': ['cai', 'caii'],
            'khoai': ['khoai', 'khoaii'],
            'chuối': ['chuoi', 'chuoii'],
            'táo': ['tao', 'taoo'],
            'cam': ['cam', 'camm'],
            'xoài': ['xoai', 'xoaii'],
            'gạo': ['gao', 'gaoo'],
            'mì': ['mi', 'mii'],
            'bún': ['bun', 'bunn'],
            'phở': ['pho', 'phoo'],
            'cơm': ['com', 'comm'],
            'đậu': ['dau', 'dauu'],
            'hạt': ['hat', 'hatt'],
            'tươi': ['tuoi', 'tuoii'],
            'khô': ['kho', 'khoo'],
            'đông': ['dong', 'dongg'],
        }
    
    def normalize_text(self, text: str) -> str:
        """Chuẩn hóa text để tìm kiếm"""
        if not text:
            return ""
        
        # Chuyển về lowercase
        text = text.lower().strip()
        
        # Loại bỏ dấu câu
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Loại bỏ khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_synonyms(self, word: str) -> Set[str]:
        """Lấy từ đồng nghĩa của một từ"""
        word = self.normalize_text(word)
        synonyms = set([word])
        
        # Tìm trong từ điển đồng nghĩa
        for key, values in self.synonyms.items():
            if word in values or word == key:
                synonyms.update(values)
                synonyms.add(key)
        
        return synonyms
    
    def get_spelling_variants(self, word: str) -> Set[str]:
        """Lấy các biến thể chính tả của một từ"""
        word = self.normalize_text(word)
        variants = set([word])
        
        # Tìm trong từ điển sửa lỗi
        for correct, incorrect_list in self.spelling_corrections.items():
            if word == correct:
                variants.update(incorrect_list)
            elif word in incorrect_list:
                variants.add(correct)
                variants.update(incorrect_list)
        
        return variants
    
    def expand_search_terms(self, query: str) -> List[str]:
        """Mở rộng từ khóa tìm kiếm với đồng nghĩa và sửa lỗi chính tả (tối ưu hóa)"""
        if not query:
            return []
        
        normalized_query = self.normalize_text(query)
        words = normalized_query.split()
        
        expanded_terms = set()
        
        # Thêm query gốc (ưu tiên cao nhất)
        expanded_terms.add(query.strip())
        expanded_terms.add(normalized_query)
        
        # Giới hạn số từ để tối ưu hiệu suất
        max_words_to_process = 3
        words_to_process = words[:max_words_to_process]
        
        # Mở rộng từng từ (giới hạn số lượng)
        for word in words_to_process:
            if len(word) >= 2:
                # Thêm từ gốc
                expanded_terms.add(word)
                
                # Thêm từ đồng nghĩa (giới hạn 3 từ đầu tiên)
                synonyms = self.get_synonyms(word)
                expanded_terms.update(list(synonyms)[:3])
                
                # Thêm biến thể chính tả (giới hạn 2 từ đầu tiên)
                variants = self.get_spelling_variants(word)
                expanded_terms.update(list(variants)[:2])
        
        # Tạo cụm từ kết hợp (chỉ cho 2 từ đầu tiên)
        if len(words) > 1:
            # Chỉ tạo 1 cụm từ chính
            phrase = f"{words[0]} {words[1]}"
            expanded_terms.add(phrase)
            
            # Thêm 1-2 biến thể của cụm từ
            synonyms1 = list(self.get_synonyms(words[0]))[:2]
            synonyms2 = list(self.get_synonyms(words[1]))[:2]
            
            for syn1 in synonyms1:
                for syn2 in synonyms2:
                    expanded_terms.add(f"{syn1} {syn2}")
                    if len(expanded_terms) > 20:  # Giới hạn tổng số terms
                        break
                if len(expanded_terms) > 20:
                    break
        
        # Loại bỏ các từ quá ngắn hoặc rỗng và giới hạn số lượng
        expanded_terms = {term for term in expanded_terms if len(term.strip()) >= 2}
        
        # Giới hạn tối đa 25 terms để tăng hiệu suất
        return list(expanded_terms)[:25]
    
    def calculate_relevance_score(self, product_name: str, product_description: str, search_query: str) -> float:
        """Tính điểm liên quan của sản phẩm với từ khóa tìm kiếm"""
        if not product_name:
            return 0.0
        
        score = 0.0
        normalized_query = self.normalize_text(search_query)
        normalized_name = self.normalize_text(product_name)
        normalized_desc = self.normalize_text(product_description or "")
        
        query_words = normalized_query.split()
        
        # Điểm cho tên sản phẩm
        if normalized_query in normalized_name:
            score += 10.0  # Khớp chính xác toàn bộ
        
        # Điểm cho từng từ trong tên
        for word in query_words:
            if word in normalized_name:
                score += 5.0
        
        # Điểm cho mô tả
        if normalized_query in normalized_desc:
            score += 3.0
        
        for word in query_words:
            if word in normalized_desc:
                score += 1.0
        
        # Điểm thưởng cho độ dài khớp
        if len(normalized_query) > 3:
            score += len(normalized_query) * 0.1
        
        return score

# Tạo instance global
fuzzy_helper = FuzzySearchHelper() 