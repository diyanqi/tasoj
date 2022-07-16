#include<cstdio>
#include<cstring>
#include<queue>
#define ll long long
using namespace std;
const ll maxn=200+5,maxm=1000+5;
ll psz=0;
struct Edge{
    ll v,w;
    Edge* next;
}pool[maxm],*head[maxn];
inline void add_edge(ll u,ll v,ll w){
    Edge *i=pool+psz++;
    i->v=v,i->w=w,i->next=head[u],head[u]=i;
}
struct pedge{
    ll dis,pos;
    bool operator<(const pedge& x) const{
        return x.dis<dis;
    }
};
ll n,m,s,t;
ll dis[maxn],cnt[maxn];bool vis[maxn];
inline void dijkstra(int s){
    priority_queue<pedge> que;
    dis[s]=0;
    que.push((pedge){0,s});
    while(!que.empty()){
        pedge u=que.top();
        que.pop();
        if(vis[u.pos])continue;
        vis[u.pos]=true;
        for(Edge *i=head[u.pos];i!=NULL;i=i->next){
            int v=i->v,w=i->w;
            if(dis[u.pos]+w<dis[v]){
                dis[v]=dis[u.pos]+w;
                if(!vis[v]){
                    que.push((pedge){dis[v],v});
                }
            }
        }
    }
}
int main(){
    scanf("%lld%lld%lld%lld",&n,&m,&s,&t);
    memset(dis,0x3f,sizeof(dis));
    while(m--){
        ll u,v,w;
        scanf("%lld%lld%lld",&u,&v,&w);
        add_edge(u,v,w);
        add_edge(v,u,w);
    }
    dijkstra(s);
    printf("%lld\n",dis[t]);
    return 0;
}