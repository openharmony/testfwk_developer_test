#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <iostream>
#include <unistd.h>


extern "C" void __gcov_dump();

using namespace std;
void sighandler(int signo)
{
    cout << "######gcov_dump_start" << endl;
    __gcov_dump();
    cout << "######gcov_dump_end" << endl;
}
__attribute__ ((constructor))
void ctor()
{
    int sigs[] = {
    SIGUSR2
    };
    int i;
    struct sigaction sa;
    sa.sa_handler = sighandler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;
    for (i = 0; i < sizeof (sigs)/ sizeof (sigs[0]); ++i){
        if (sigaction(sigs[i], &sa, NULL) == -1){
            cout << "Could not set signal handler" << endl;
        }
    }
}

