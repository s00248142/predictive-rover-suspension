/*******************************************************************************
* File Name: app.h
* Description: Link between main.c and app.c
* 	'target_speed' control from CAN is the primary parameter passed into app.c
* Programmer: Alan Ryan (s00248142)
* Date: 06/05/2025
* Version: 1.0
*******************************************************************************/

#include <stdint.h>   // needed for int16_t

extern int16_t target_speed; // Primary parameter to be linked.

#ifndef APP_H
#define APP_H

void app_init(void);
void app_loop(void);

#endif

/******************************* End of file **********************************/