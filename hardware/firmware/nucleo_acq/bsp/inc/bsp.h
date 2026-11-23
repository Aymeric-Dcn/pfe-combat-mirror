/*
 * bsp.h
 *
 *  Created on: Feb 28, 2025
 *      Author: User
 */

#ifndef INC_BSP_H_
#define INC_BSP_H_

#include "stm32f0xx.h"

/*
 * LED driver functions
 */

void	BSP_LED_Init		(void);
void	BSP_LED_On			(void);
void	BSP_LED_Off			(void);
void	BSP_LED_Toggle		(void);


/*
 * Push-Button driver functions
 */

void       BSP_PB_Init		(void);
uint8_t    BSP_PB_GetState	(void);

/*
 * Debug Console init
 */

void	BSP_Console_Init	(void);
uint8_t	BSP_Console_SendDMA	(uint8_t *buffer, uint16_t nbytes);

/*
 * ADC functions
 */
#define ADC_NB_CHANNELS		6

void BSP_ADC_Init			(void);
void BSP_ADC_Resync			(void);

/*
 * Timer functions
 */
void BSP_TIMER_Timebase_Init	(void);
void BSP_TIMER_Trigger_Init		(void);
void BSP_TIMER_IC_Init			(void);
/*
 * Timer delays
 */

void BSP_DELAY_TIM_init		(void);
void BSP_DELAY_TIM_ms		(uint16_t ms);

/*
 * PWM Timer
 */
void BSP_TIMER_PWM_Init		(void);

/*
 * DAC initialization
 */
void BSP_DAC_Init			(void);

/*
 * NVIC initialization
 */
void BSP_NVIC_Init			(void);

/*
 * I2C initialization
 */

void BSP_I2C1_Init			(void);

void BSP_DBG_Pins_Init		(void);
/*
 * READ I2C
 */
uint8_t	BSP_I2C1_Read		( uint8_t device_address,
                       	   	   uint8_t register_address,
							   uint8_t *buffer,
							   uint8_t nbytes );
/*
 * WRITE I2C
 */

uint8_t	BSP_I2C1_Write		( uint8_t device_address,
								uint8_t register_address,
								uint8_t *buffer, uint8_t nbytes );

/*
 * SPI functions
 */
void BSP_SPI1_Init			(void);

uint8_t BSP_SPI_SendReceive	(uint8_t tx_byte);

//Function for LPS25H but can work as a general prototype
void BSP_LPS25H_Read	(uint8_t register_address,
							uint8_t *buffer,
							uint8_t nbytes);

void BSP_LPS25H_Write(uint8_t register_address,
						uint8_t data);

#endif /* INC_BSP_H_ */
