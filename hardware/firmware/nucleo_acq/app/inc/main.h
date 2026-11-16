/*
 * main.h
 *
 *  Created on: Feb 26, 2025
 *      Author: User
 */

#ifndef INC_MAIN_H_
#define INC_MAIN_H_
#include "stm32f0xx.h"

/*
 * printf() and sprintf() from printf-stdarg.c
 */

int my_printf	(const char *format, ...);
int my_sprintf	(char *out, const char *format, ...);

#endif /* INC_MAIN_H_ */
