from __future__ import annotations


CATEGORY_NORMALIZATION = {
    "FOOD_DINING": "푸드/외식",
    "MART_SHOPPING": "마트/쇼핑",
    "CAFE_DESSERT": "카페/디저트",
    "EDUCATION_CHILDCARE": "교육/육아",
    "UTILITIES": "공과금/생활요금",
    "SUBSCRIPTION_MEMBERSHIP": "구독/멤버십",
    "BEAUTY_FITNESS": "뷰티/피트니스",
    "MOVIE_CULTURE": "영화/문화",
    "AUTO_MAINTENANCE": "자동차/정비",
    "AIRLINE_MILEAGE": "항공/마일리지",
    "OVERSEAS": "해외",
    "OTHER": "기타",
    "ALL_MERCHANTS": "모든가맹점",
    "THEMEPARK_LEISURE": "테마파크/레저",
    "DEPARTMENT_STORE": "백화점",
    "PREMIUM_SERVICE": "프리미엄서비스",
    "CASHBACK": "캐시백",
    "MEMBERSHIP_POINTS": "멤버십/포인트",
    "DELIVERY": "배달앱", "배달": "배달앱", "배달앱": "배달앱",
    "MART": "마트/쇼핑", "마트": "마트/쇼핑", "대형마트": "마트/쇼핑",
    "쇼핑": "마트/쇼핑", "마트/쇼핑": "마트/쇼핑",
    "TUITION": "교육/육아", "교육": "교육/육아", "학원": "교육/육아",
    "육아": "교육/육아", "교육/육아": "교육/육아", "ACADEMY": "교육/육아",
    "CHILD_CLASS": "교육/육아", "ONLINE_COURSE": "교육/육아",
    "BABY": "교육/육아", "BOOKS": "교육/육아",
    "CAFE": "카페/디저트", "카페": "카페/디저트",
    "디저트": "카페/디저트", "카페/디저트": "카페/디저트",
    "DINING": "푸드/외식", "RESTAURANT": "푸드/외식",
    "음식점": "푸드/외식", "외식": "푸드/외식", "푸드/외식": "푸드/외식",
    "FITNESS": "뷰티/피트니스", "BEAUTY": "뷰티/피트니스",
    "헬스": "뷰티/피트니스", "피트니스": "뷰티/피트니스",
    "뷰티/피트니스": "뷰티/피트니스",
    "FUEL": "주유", "GAS": "주유", "주유": "주유",
    "INSURANCE": "보험", "보험": "보험",
    "CONVENIENCE": "편의점", "편의점": "편의점",
    "TRANSPORT": "교통", "TRANSIT": "교통", "TAXI": "교통",
    "PARKING": "교통", "TOLL": "교통", "교통": "교통",
    "MEDICAL": "병원/약국", "병원": "병원/약국", "약국": "병원/약국",
    "병원/약국": "병원/약국", "PHARMACY": "병원/약국",
    "STATIONERY": "문구", "문구": "문구",
    "SHOPPING": "마트/쇼핑", "GROCERY": "마트/쇼핑",
    "ONLINE_GROCERY": "마트/쇼핑", "ONLINE_SHOPPING": "온라인쇼핑",
    "SUBSCRIPTION": "구독/멤버십", "TELECOM": "통신",
    "HOUSEHOLD": "생활", "LIVING": "생활", "FURNITURE": "생활",
    "MANAGEMENT_FEE": "공과금/생활요금", "EASY_PAY": "간편결제",
    "AUTO": "자동차/정비", "RENTAL_CAR": "자동차/정비",
    "LODGING": "여행/숙박", "TRAVEL": "여행/숙박",
    "TRAVEL_LODGING": "여행/숙박", "TRAVEL_SPEND": "여행/숙박",
    "TRAVEL_TRANSIT": "여행/숙박", "TRAVEL_TRANSPORT": "여행/숙박",
    "MOVIE": "영화/문화", "영화/문화": "영화/문화",
}


def normalize_payment_category(category: str | None) -> str | None:
    if not category:
        return None
    value = category.strip()
    return CATEGORY_NORMALIZATION.get(
        value,
        CATEGORY_NORMALIZATION.get(value.upper(), value),
    )
