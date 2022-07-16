s1=input()
s2=input()
x={}
n=0
for i in s2:
    if(i in s1):
        n+=1
        x[i]=x.get(i,0)+1
# for i in s1:
#     print(f"{i}-{x.get(i,0)}")
print(n)