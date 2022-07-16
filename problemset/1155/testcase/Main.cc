#include<bits/stdc++.h>
using namespace std;
long long n,s;
int main()
{
    cin>>n;
    for(int i=1;i<=n;i++)
    {
        for(int j=1;j<=i;j++)
        {s++;cout<<s<<'*';}
        cout<<endl;
    }
    return 0;
}
