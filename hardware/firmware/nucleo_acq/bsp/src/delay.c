/*
 * delay.c
 *
 *  Created on: Mar 1, 2025
 *      Author: User
 */


#include "delay.h"

/*
 *  Basic delay functions
 */

void BSP_DELAY_ms(uint32_t delay)
{
	uint32_t	i;
	for(i=0; i<(delay*2500); i++);		// Tuned for ms at 48MHz
}

void BSP_DELAY_us(uint32_t delay)
{
	uint32_t	i;
	for(i=0; i<(delay*3); i++);		// Tuned for µs at 48MHz
}

/*
 * timer_delay_init()
 * Initialize TIM6 with 1ms counting period
 * ARR is set to maximum value -> delay [2ms-65s]
 */

void BSP_DELAY_TIM_init(void)
{
	// Enable TIM6 clock
	RCC->APB1ENR |= RCC_APB1ENR_TIM6EN;

	// Reset TIM6 configuration
	TIM6->CR1 = 0x0000;
	TIM6->CR2 = 0x0000;

	// Set TIM6 prescaler
	// Fck = 48MHz -> /48000 = 1KHz counting frequency
	TIM6->PSC = (uint16_t) 48000 -1;

	// Set ARR to maximum value
	TIM6->ARR = (uint16_t) 0xFFFF;
}

/*
 * timer_delay_ms(uint16_t ms)
 * waits here for ms
 */
void BSP_DELAY_TIM_ms(uint16_t ms)
{
	// Resets TIM6 counter
	TIM6->EGR |= TIM_EGR_UG;

	// Start TIM6 counter
	TIM6->CR1 |= TIM_CR1_CEN;

	// Wait until TIM6 counter reaches delay
	while(TIM6->CNT < ms);

	// Stop TIM6 counter
	TIM6->CR1 &= ~TIM_CR1_CEN;
}


