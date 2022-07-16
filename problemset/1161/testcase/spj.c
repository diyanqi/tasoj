#include <stdio.h>
#include <math.h>

double x;
double answer;
int ret=0;
int main(int argc, char **argv)
{
	FILE *fpout = fopen(argv[3], "r");
	FILE *fpans = fopen(argv[2], "r");
	//FILE *fpscore = fopen(argv[4], "w");

	fscanf(fpout, "%lf", &x);
	fscanf(fpans, "%lf", &answer);

	if (fabs(x - answer) <= 1e-4)
		;	//fprintf(fpscore, "10\n");
	else
		ret=1;//fprintf(fpscore, "0\n");

	fclose(fpout);
	fclose(fpans);
	//fclose(fpscore);

	return ret;
}
