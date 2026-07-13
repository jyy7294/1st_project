import random
trial = 0
history = []
while True:
    lotto = []
    num = int(input("1) 추첨 2) 이력 보기 3) 종료"))
    if num == 1:
        trial += 1
        b = 0
        while b < 6:
            a = random.randint(1,45)
            lotto.append(a)
            b += 1
        lotto.sort()
        history.append(lotto)
        print("추천 로또번호 :",end=" ")
        for a in lotto:
            print(a,end=" ")
        print()
        #lotto.clear()
    elif num == 2:
        print("추천된 과거 이력")
        if trial == 0:
            print("추천된 과거 이력이 없습니다.")
            break
        print(f"{trial}회 : ",end="")
        c = 0
        while c < 5:
            last = history.pop()
            print(f"{trial}회 : ",end="")
            c = 0
            while c < 5:
                last = history.pop()
                print(f"{trial}회 : ",end="")
                print(last)
        else:
            print("메뉴를 종료합니다.")
            break
     