#include<stdio.h>
#include<math.h>
int main(int argc,char ** argv){
    FILE *fo=fopen(argv[2],"r");
    FILE *fu=fopen(argv[3],"r");
//    FILE *fd=fopen("diff.out","w");
    double o,u;
    while(fscanf(fo,"%lf",&o)!=EOF){
	if(EOF!=fscanf(fu,"%lf",&u)){
	   if(fabs(u-o)>1e-2){
	//	fprintf(fd,"%s\nout:%lf your:%lf\n",argv[1],o,u);		
	//	fclose(fd);
		return 1;
	   }
	}else{
		return 1;
	}

    }
    return 0;
}
