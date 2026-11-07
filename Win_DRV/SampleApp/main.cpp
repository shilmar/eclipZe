//================================================================================================
// Copyright Nikon Corporation - All rights reserved
//
// View this file in a non-proportional font, tabs = 3
//================================================================================================

#include <iostream>
#include <mutex>
#include "Maid3d1.h"
#include "Maid3.h"
#include "CtrlSample.h"
using namespace std;

LPMAIDEntryPointProc	g_pMAIDEntryPoint = NULL;
LPMAIDInitializeSDKProc g_pMAIDInitializeSDK = NULL;
LPMAIDFreeSDKProc g_pMAIDFreeSDK = NULL;
LPMAIDConnectDeviceProc g_pMAIDConnectDevice = NULL;
LPMAIDDisconnectDeviceProc g_pMAIDDisconnectDevice = NULL;
LPMAIDStartLiveView g_pMAIDStartLiveView = NULL;
LPMAIDStopLiveView g_pMAIDStopLiveView = NULL;
LPMAIDGetLiveViewStatus g_pMAIDGetLiveViewStatus = NULL;
LPMAIDGetLoggingLevel g_pMAIDGetLoggingLevel = NULL;
LPMAIDSetLoggingLevel g_pMAIDSetLoggingLevel = NULL;
LPMAIDStartShooting g_pMAIDStartShooting = NULL;
LPMAIDGetShootingStatus g_pMAIDGetShootingStatus = NULL;
LPMAIDGetRemainingShootCount g_pMAIDGetRemainingShootCount = NULL;
LPMAIDCancelShooting g_pMAIDCancelShooting = NULL;
LPMAIDGetCapability g_pMAIDGetCapability = NULL;
LPMAIDSetCapability g_pMAIDSetCapability = NULL;
LPMAIDEnumCapabilities g_pMAIDEnumCapabilities = NULL;
LPMAIDEnumDevices g_pMAIDEnumDevices = NULL;
LPMAIDStartMovieRecording g_pMAIDStartMovieRecording = NULL;
LPMAIDStopMovieRecording g_pMAIDStopMovieRecording = NULL;
LPMAIDStartOperation g_pMAIDStartOperation = NULL;
LPNkMAIDEnumDevices pDeviceList = NULL;
LPMAIDSetImageVideoSavePath g_pMAIDSetImageVideoSavePath = NULL;
//make connected deviceid global
NkMAIDDeviceInfo connectedDevice;

LPNkMAIDEnumCapInfo pEnumCapInfo = NULL;

UCHAR	g_bFileRemoved = FALSE;
ULONG	g_ulCameraType = 0;	// CameraType

LPVOID pCapValue = NULL;
eNkMAIDDataType eDataType;

HINSTANCE	g_hInstModule = NULL;

std::mutex device_list_lock;
std::mutex m_capability_list_lock;

#define LIBRARY "ControlServiceLayer.dll"

int main()
{
	char	buf[256];
	ULONG	ulModID = 0, ulSrcID = 0;
	UWORD	wSel;
	BOOL	bRet;
	bRet = Load_Module(LIBRARY);

	if (bRet == FALSE) {
		puts("Failed in loading \"TypeCommon Module\".\n");
		return -1;
	}
#if _DEBUG
	eNkMAIDLoggingLevel eLoggingLevel = kkNkSDKLogLevel_SystemError;
#else
	eNkMAIDLoggingLevel eLoggingLevel = kkNkSDKLogLevel_Error;
#endif	
	NKERROR lerror = g_pMAIDSetLoggingLevel(eLoggingLevel);
	if (lerror == kNkMAIDResult_NoError)
	{
		eLoggingLevel = kkNkSDKLogLevel_SystemError;
		HRESULT hRes = g_pMAIDGetLoggingLevel(eLoggingLevel);
		if (hRes == S_OK)
		{
			printf("Logging Level = %s\n", (eLoggingLevel == kkNkSDKLogLevel_SystemError ? "SystemError" : (eLoggingLevel == kkNkSDKLogLevel_Error ? "Error" : "Debug")));
		}
		else
		{
			printf("GetLoggingLevel API failed\n");
		}
	}
	else
	{
		printf("SetLoggingLevel API failed\n");
	}

	NkMAIDCSCallback callback;
	callback.pfnEventProc = (LPNKFUNC)SrcEventProc;
	callback.pUIReqProc = (LPNKFUNC)UIRequestProc;
	callback.pProgressProc = (LPNKFUNC)ProgressProc;
	callback.pDataProc = (LPNKFUNC)DataProc;
	callback.pLiveViewDataProc = (LPNKFUNC)LVDataProc;
	callback.refProc = NULL;

	device_list_lock.lock();
	lerror = g_pMAIDInitializeSDK((LPMAIDAllocateMemory)AllocateMemory, (LPMAIDFreeMemory)FreeMemory, &callback, &pDeviceList, NULL);
	device_list_lock.unlock();

	if (lerror != kNkMAIDResult_NoError)
	{
		puts("Unable to Initialize SDK.\n");
		return -1;
	}

	CreateDirectoryW(L"preview", NULL);
	lerror = g_pMAIDSetImageVideoSavePath(L"preview", L"preview");

	while (1)
	{
		printf("\nSelect (1, 0)\n");
		printf(" 1. Select Device\n");
		printf(" 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:// Children
		{
			int availableDevices = 0;

			device_list_lock.lock();
			if (pDeviceList == NULL || pDeviceList->ulElements == 0)
			{
				//UnLock pDeviceList
				puts("No device present.\n");
				//should be there in while loop
				device_list_lock.unlock();
				break;
			}

			for (ULONG i = 0; i < pDeviceList->ulElements; i++)
			{
				printf("Index = %d, Device Id = %d, Device Name = %s, Available = %s\n",
					i + 1, pDeviceList->pDeviceData[i].ID, pDeviceList->pDeviceData[i].Name,
					(pDeviceList->pDeviceData[i].Availability ? "True" : "False"));

				if (pDeviceList->pDeviceData[i].Availability == TRUE)
					availableDevices++;
			}

			//when atleast 1 device is available then user should not get option to enter value

			if (availableDevices == 0)
			{
				device_list_lock.unlock();
				break;
			}

			printf("\nselect the device\n");
			printf("Please enter the device Index\n > ");
			scanf("%s", buf);
			wSel = atoi(buf);

			if (wSel > pDeviceList->ulElements || pDeviceList->pDeviceData[wSel - 1].Availability == FALSE)
			{
				device_list_lock.unlock();
				break;
			}

			lerror = g_pMAIDConnectDevice(pDeviceList->pDeviceData[wSel - 1].ID, &pEnumCapInfo);
			if (lerror != kNkMAIDResult_NoError)
			{
				printf("Unable to Connect with Device.\n");
				device_list_lock.unlock();
			}
			else
			{
				connectedDevice = pDeviceList->pDeviceData[wSel - 1];
				device_list_lock.unlock();
				ULONG ulSaveMedia = kNkMAIDSaveMedia_Card_SDRAM;
				g_pMAIDSetCapability(kNkMAIDCapability_SaveMedia, (LPVOID)&ulSaveMedia, kNkMAIDDataType_UnsignedPtr);
				SourceCommandLoop(connectedDevice.ID);
			}

			m_capability_list_lock.lock();

			if (pEnumCapInfo)
			{
				free(pEnumCapInfo->pCapArray);
				free(pEnumCapInfo);
				pEnumCapInfo = NULL;
			}

			m_capability_list_lock.unlock();

			break;
		}
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}

	HRESULT hRes = g_pMAIDFreeSDK();
	if (hRes == S_OK)
		printf("\nSDK is now closed.\n");
	else printf("\nUnable to close SDK.\n");

	//Free pDeviceList
	if (pDeviceList)
	{
		if (pDeviceList->pDeviceData)
			free(pDeviceList->pDeviceData);
		free(pDeviceList);
		pDeviceList = NULL;
	}

	FreeLibrary(g_hInstModule);
	g_hInstModule = NULL;
	return 0;
}

BOOL SourceCommandLoop(ULONG ulSrcID)
{
	char	buf[256];
	UWORD	wSel;
	BOOL bRet;

	while (1)
	{
		printf("\nSelect (1-11, 0)\n");
		printf(" 1. Camera settings(1)        2. Camera settings(2)         3. Shooting Menu\n");
		printf(" 4. Live View                 5. Autofocus                  6. Capture\n");
		printf(" 7. CaptureAsync              8. AFCaptureAsync		    9. AFCapturesync\n");
		printf("10. SB Menu		     11. MovieMenu	            0. Exit\n > ");
		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:// Camera setting 1
			bRet = SetUpCamera1();
			break;
		case 2:// Camera setting 2
			bRet = SetUpCamera2();
			break;
		case 3:// Shooting Menu
			bRet = SetShootingMenu();
			break;
		case 4:// Live View
			bRet = SetLiveView();
			break;
		case 5:// AutoFocus
			if (!CheckCapability(kNkMAIDCapability_AutoFocus, kNkMAIDCapOperation_Start))
			{
				break;
			}

			if (g_pMAIDStartOperation(kNkMAIDCapability_AutoFocus, NULL, NULL) != kNkMAIDResult_NoError)
				printf("Unable start autofous.");
			break;
		case 6:// Capture
		{
			CaptureSync();
		}
		break;
		case 7:// CaptureAsync
		{
			CaptureAsync();
		}
		break;
		case 8:// AFCaptureAsync
		{
			CaptureAFAsync();
		}
		break;
		case 9:
		{
			CaptureAFSync();
		}
		break;
		case 10:// SB Menu
		{
			bRet = SetSBMenu();
		}
		break;
		case 11:
		{
			SetMovieMenu();
		}
		break;
		case 12:
		{
			NKERROR err = g_pMAIDStartLiveView(NULL, NULL);
			if (err == kNkMAIDResult_NoError)
			{
				Sleep(350);
				g_pMAIDStopLiveView(NULL, NULL);
				printf("\n[SDK] LiveView preview frame captured to preview/last_preview.jpg\n");
			}
			else
			{
				printf("\n[SDK] StartLiveView failed: %d\n", err);
			}
			break;
		}
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
			{
				HRESULT hRes = g_pMAIDDisconnectDevice();
				if (hRes == S_FALSE)
				{
					printf("\nUnable to free device.\n");
					return -1;
				}
				else printf("\nDevice is free now.\n");
				break;
			}
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL CaptureAsync()
{
	char	buf[256];
	UWORD	wSel;
	NKERROR lerror;

	while (1)
	{
		printf("\nSelect (1-8, 0)\n");
		printf(" 1. Single Shooting       2. Continuous Shooting\n");
		printf(" 3. Interval Shooting     4. SelfTimer Shooting\n");
		printf(" 5. Bulb Shooting         6. Cancel Shooting\n");
		printf(" 7. BulbInterval\t  8. Focus Shift\n");
		printf(" 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:// CaptureAsync single
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			//Single Shooting
			printf("Single Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSingle;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for second release.\n");
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start single shooting.\n");
		}
		break;
		case 2:				//continuous shooting
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;

			printf("continuous Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeContinuous;
			printf("Enter Num Shots (default 5):\n > ");
			scanf("%s", buf);
			int nShots = atoi(buf);
			stShootParam.ulContinuous_Interval_NumShots = (nShots > 0) ? nShots : 5;

			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start continuous shooting.\n");
			else
			{
				while (ulErr == kNkMAIDResult_Pending)
				{
					Sleep(100);
					ULONG ulRemShoot;
					hRes = g_pMAIDGetRemainingShootCount(ulRemShoot);
					if (hRes == S_OK) printf("Remaining Shoot count = %d\n", ulRemShoot);
					else printf("GetRemainingShootCount Api failed.\n");

					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
				}
			}
		}
		break;
		case 3:						//Interval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;
			printf("Interval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeInterval;
			stShootParam.ulShootingStartTimeFromNow = 5;
			stShootParam.ulIntervalTime = 10;
			stShootParam.ulContinuous_Interval_NumShots = 3;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start Interval shooting.\n");
			else
			{
				do
				{

					ULONG ulRemShoot;
					hRes = g_pMAIDGetRemainingShootCount(ulRemShoot);
					if (hRes == S_OK) printf("Remaining Shoot count = %d\n", ulRemShoot);
					else printf("RemainingShootCount API failed\n");

					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
					Sleep(100);

				} while (ulErr == kNkMAIDResult_Pending);
			}
		}
		break;
		case 4:							//Self Timer
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;
			printf("Self timer Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSelfTimer;
			stShootParam.ulShootingStartTimeFromNow = 5;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start self timer shooting.\n");
			else
			{
				do
				{
					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
					Sleep(10);

				} while (ulErr == kNkMAIDResult_Pending);
			}
		}
		break;
		case 5:					//Bulb
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;

			printf("Bulb Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeBULB;
			stShootParam.ulBULBExposureDuration = 10;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);

			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for second release.\n");
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start bulb shooting.\n");
			else
			{
				while (ulErr == kNkMAIDResult_Pending)
				{
					Sleep(10);
					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
				}
			}
		}
		break;
		case 6:
		{
			lerror = g_pMAIDCancelShooting(NULL, NULL);
			if (lerror != kNkMAIDResult_NoError)
				printf("Issue in cancelling.\n");
			else
				printf("Shoot cancel successful\n");
		}
		break;
		case 7:						//BULBInterval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("BULBInterval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeBULBInterval;
			stShootParam.ulShootingStartTimeFromNow = 3;
			stShootParam.ulIntervalTime = 5;
			stShootParam.ulBULBExposureDuration = 5;
			stShootParam.ulContinuous_Interval_NumShots = 10;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);

			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for second release.\n");
			if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start BULBInterval shooting.\n");
		}
		break;
		case 8:
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			//Single Shooting
			printf("Focus Shift Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeFocusShift;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for second release.\n");
			if (lerror != kNkMAIDResult_NoError) printf("Unable to focus shift shooting.\n");
		}
		break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL CaptureSync()
{
	char	buf[256];
	UWORD	wSel;
	NKERROR lerror;

	while (1)
	{
		printf("\nSelect (1-6, 0)\n");
		printf(" 1. Single Shooting           2. Continuous Shooting\n");
		printf(" 3. Interval Shooting         4. SelfTimer Shooting\n");
		printf(" 5. Bulb Shooting             6. IntervalBulb Shooting\n");
		printf(" 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1://  single
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			//Single Shooting
			printf("Single Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSingle;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start single shooting.\n");
		}
		break;

		case 2:				//Continuous shooting
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			printf("Continuous Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeContinuous;
			printf("Enter Num Shots (default 5):\n > ");
			scanf("%s", buf);
			int nShots = atoi(buf);
			stShootParam.ulContinuous_Interval_NumShots = (nShots > 0) ? nShots : 5;

			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start Continuous shooting.\n");
		}
		break;
		case 3:						//Interval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("Interval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeInterval;
			stShootParam.ulShootingStartTimeFromNow = 3;
			stShootParam.ulIntervalTime = 4;
			stShootParam.ulContinuous_Interval_NumShots = 3;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start Interval shooting.\n");
		}
		break;
		case 4:							//Self Timer
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("Self timer Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSelfTimer;
			stShootParam.ulShootingStartTimeFromNow = 5;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start self timer shooting.\n");
		}
		break;
		case 5:					//Bulb
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			printf("Bulb Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeBULB;
			stShootParam.ulBULBExposureDuration = 5;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start Bulb shooting.\n");
		}
		break;
		case 6:						//BULBInterval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("Interval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeBULBInterval;
			stShootParam.ulShootingStartTimeFromNow = 3;
			stShootParam.ulIntervalTime = 10;
			stShootParam.ulBULBExposureDuration = 5;
			stShootParam.ulContinuous_Interval_NumShots = 3;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start BulbInterval shooting.\n");
		}
		break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL AFSettings()
{
	char	buf[256];
	UWORD	wSel;
	BOOL bRet;

	while (1)
	{
		printf("\nSelect (1-8, 0)\n");
		printf("1. ContrastAF         2. ContrastAFArea           3. MovieFocusMode\n");
		printf("4. MovieAfAreaMode    5. AFcPriority              6. AFsPriority\n");
		printf("7. AFAreaSelector     8. AFAreaPoint              0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:
			bRet = SetUnsignedIntCapability(kNkMAIDCapability_ContrastAF, pCapValue, eDataType);
			break;

		case 2:
			bRet = SetPointCapability(kNkMAIDCapability_ContrastAFArea);
			break;

		case 3:
			bRet = SetEnumCapability(kNkMAIDCapability_MovieFocusMode, pCapValue, eDataType);
			break;

		case 4:
			bRet = SetEnumCapability(kNkMAIDCapability_MovieAfAreaMode, pCapValue, eDataType);
			break;

		case 5: //kNkMAIDCapability_AFcPriority
			bRet = SetEnumCapability(kNkMAIDCapability_AFcPriority, pCapValue, eDataType);
			break;

		case 6: //kNkMAIDCapability_AFsPriority
			bRet = SetEnumCapability(kNkMAIDCapability_AFsPriority, pCapValue, eDataType);
			break;

		case 7: //kNkMAIDCapability_AFAreaSelector
			bRet = SetEnumCapability(kNkMAIDCapability_AFAreaSelector, pCapValue, eDataType);
			break;

		case 8: //kNkMAIDCapability_AFAreaPoint
			bRet = SetUnsignedIntCapability(kNkMAIDCapability_AFAreaPoint, pCapValue, eDataType);
			break;

		case 0:
			return TRUE;

		default:
			printf("\n Wrong Choice\n");
			break;
		}
	}
	return TRUE;
}

BOOL CaptureAFAsync()
{
	char	buf[256];
	UWORD	wSel;
	NKERROR lerror;

	while (1)
	{
		printf("\nSelect (1-6, 0)\n");
		printf(" 1. Single Shooting       2. Continuous Shooting\n");
		printf(" 3. Interval Shooting     4. SelfTimer Shooting\n");
		printf(" 5. Cancel Shooting       6. BulbInterval\n");
		printf(" 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:// CaptureAsync single
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;

			//Single Shooting
			printf("Single Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSingle;
			stShootParam.bAutoFocus = true;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for second release.\n");
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start single shooting.\n");
			else
			{
				while (ulErr == kNkMAIDResult_Pending)
				{
					Sleep(10);
					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
				}
			}
		}
		break;
		case 2:				//continuous shooting
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;

			printf("continuous Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeContinuous;
			stShootParam.ulContinuous_Interval_NumShots = 4;
			stShootParam.bAutoFocus = true;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start continuous shooting.\n");
			else
			{
				while (ulErr == kNkMAIDResult_Pending)
				{
					Sleep(100);
					ULONG ulRemShoot;
					hRes = g_pMAIDGetRemainingShootCount(ulRemShoot);
					if (hRes == S_OK) printf("Remaining Shoot count = %d\n", ulRemShoot);
					else printf("GetRemainingShootCount Api failed.\n");

					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
				}
			}
		}
		break;
		case 3:						//Interval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;
			printf("Interval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeInterval;
			stShootParam.ulShootingStartTimeFromNow = 5;
			stShootParam.ulIntervalTime = 10;
			stShootParam.ulContinuous_Interval_NumShots = 3;
			stShootParam.bAutoFocus = true;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start Interval shooting.\n");
			else
			{
				do
				{

					ULONG ulRemShoot;
					hRes = g_pMAIDGetRemainingShootCount(ulRemShoot);
					if (hRes == S_OK) printf("Remaining Shoot count = %d\n", ulRemShoot);
					else printf("RemainingShootCount API failed\n");

					//if (ulRemShoot <= 2)
					//	lerror = g_pMAIDCancelShooting(NULL, NULL);
					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
					Sleep(100);

				} while (ulErr == kNkMAIDResult_Pending);
			}
		}
		break;
		case 4:							//Self Timer
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			HRESULT hRes;
			printf("Self timer Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSelfTimer;
			stShootParam.ulShootingStartTimeFromNow = 5;
			ULONG ulErr = kNkMAIDResult_Pending;
			stShootParam.bAutoFocus = true;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);
			if (lerror != kNkMAIDResult_NoError) printf("Unable to start self timer shooting.\n");
			else
			{
				do
				{
					hRes = g_pMAIDGetShootingStatus(ShootingStatus);
					if (hRes == S_OK)
						printf("Shooting status = %d \n", ShootingStatus);
					else
						printf("GetShootingStatus Api failed.\n");
					Sleep(10);

				} while (ulErr == kNkMAIDResult_Pending);
			}
		}
		break;
		case 5:
		{
			lerror = g_pMAIDCancelShooting(NULL, NULL);
			if (lerror != kNkMAIDResult_NoError)
				printf("Issue in cancelling.\n");
			else
				printf("Shoot cancel successful\n");
		}
		break;
		case 6:						//BULBInterval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("BULBInterval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeBULBInterval;
			stShootParam.ulShootingStartTimeFromNow = 3;
			stShootParam.ulIntervalTime = 5;
			stShootParam.ulBULBExposureDuration = 5;
			stShootParam.ulContinuous_Interval_NumShots = 10;
			stShootParam.bAutoFocus = true;
			ULONG ulErr = kNkMAIDResult_Pending;
			lerror = g_pMAIDStartShooting(stShootParam, (LPMAIDAsyncCompletionProc)CompProc, (NKREF)&ulErr);

			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for second release.\n");
			if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start BULBInterval shooting.\n");
		}
		break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}

	}
	return true;
}

BOOL CaptureAFSync()
{
	char	buf[256];
	UWORD	wSel;
	NKERROR lerror;

	while (1)
	{
		printf("\nSelect (1-4, 0)\n");
		printf(" 1. Single Shooting		2. Continuous Shooting\n");
		printf(" 3. Interval Shooting		4. SelfTimer Shooting\n");
		printf(" 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1://  single
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			//Single Shooting
			printf("Single Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.bAutoFocus = true;
			stShootParam.ShootingType = kNkSDKShootingTypeSingle;
			ULONG ulErr = kNkMAIDResult_NoError;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start single shooting.\n");
		}
		break;
		case 2:				//Continuous shooting
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;

			printf("Continuous Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
			stShootParam.bAutoFocus = true;
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeContinuous;
			stShootParam.ulContinuous_Interval_NumShots = 4;

			ULONG ulErr = kNkMAIDResult_NoError;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start Continuous shooting.\n");
		}
		break;
		case 3:						//Interval
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("Interval Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
			stShootParam.bAutoFocus = true;
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeInterval;
			stShootParam.ulShootingStartTimeFromNow = 3;
			stShootParam.ulIntervalTime = 4;
			stShootParam.ulContinuous_Interval_NumShots = 3;
			ULONG ulErr = kNkMAIDResult_NoError;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start interval shooting.\n");
		}
		break;
		case 4:							//Self Timer
		{
			MAIDShootingStructure stShootParam;
			eNkMAIDShootingStatus ShootingStatus = kNkSDKShootingFinishedOrNotStarted;
			printf("Self timer Shooting\n");
			memset(&stShootParam, 0, sizeof(MAIDShootingStructure));
			stShootParam.bAutoFocus = true;
#ifdef _WIN32
			wcscpy(stShootParam.ImageSavePath, L"preview");//give a directory path
#else
			strcpy(stShootParam.ImageSavePath, "preview");//give a directory path
#endif
			stShootParam.ShootingType = kNkSDKShootingTypeSelfTimer;
			stShootParam.ulShootingStartTimeFromNow = 5;
			ULONG ulErr = kNkMAIDResult_NoError;
			lerror = g_pMAIDStartShooting(stShootParam, NULL, NULL);
			if (lerror == kNkMAIDResult_Waiting_2ndRelease)
				printf("Waiting for 2nd Release.\n");
			else if (lerror != kNkMAIDResult_NoError)
				printf("Unable to start seltimer shooting.\n");
		}
		break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL SetUpCamera1()
{
	char	buf[256];
	UWORD	wSel;
	NKERROR lerror;

	while (1)
	{
		printf("\nSelect the item you want to set up\n");

		printf(" 1. IsAlive			 2. Name				 3. Interface\n");
		printf(" 4. DataTypes			 5. BatteryLevel			 6. LockExposure\n");
		printf(" 7. ExposureMode		 8. ShutterSpeed			 9. Aperture\n");
		printf("10. ExposureComp		11. SaveMedia				12. MovieWBAutoType\n");
		printf("14. MovieAperture		15. MovieExposureComp\n");
		printf("19. LensType			21. MovieShutterSpeed                   24. EnableBracketing\n");
		printf("25. BracketingOrder		26. AEBracketingStep			27. WBBracketingStep\n");
		printf("28. BracketingType		29. ADLBracketingType			30. ADLBracketingStep\n");
		printf("31. BracketingCount		32. BracketingVary			 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:// IsAlive
			SetBoolCapability(kNkMAIDCapability_IsAlive, pCapValue, eDataType);
			break;

		case 2:// Name
			SetStringCapability(kNkMAIDCapability_Name, pCapValue, eDataType);
			break;

		case 3:// Interface
			SetStringCapability(kNkMAIDCapability_Interface, pCapValue, eDataType);
			break;

		case 4:// DataTypes
			SetUnsignedIntCapability(kNkMAIDCapability_DataTypes, pCapValue, eDataType);
			break;

		case 5:// BatteryLevel
			SetIntegerCapability(kNkMAIDCapability_BatteryLevel, pCapValue, eDataType);
			break;

		case 6:// LockExposure
			SetBoolCapability(kNkMAIDCapability_LockExposure, pCapValue, eDataType);
			break;

		case 7:// ExposureMode
			SetEnumCapability(kNkMAIDCapability_ExposureMode, pCapValue, eDataType);
			break;

		case 8:// ShutterSpeed(Exposure Time)
			SetEnumCapability(kNkMAIDCapability_ShutterSpeed, pCapValue, eDataType);
			break;

		case 9:// Aperture(F Number)
			SetEnumCapability(kNkMAIDCapability_Aperture, pCapValue, eDataType);
			break;

		case 10:// ExposureCompensation
		{
			NkMAIDRange	stRange = { 0 };
			double lfValue;
			char buf[256];

			lerror = g_pMAIDGetCapability(kNkMAIDCapability_ExposureComp, kNkSDKGetSettingValue, pCapValue, eDataType);
			if (eDataType != kNkMAIDDataType_RangePtr)
			{
				printf("\nInvalid value returned \n");   freeByDataType(pCapValue, eDataType);
				break;
			}
			if (lerror == kNkMAIDResult_NoError && pCapValue != NULL)
			{
				stRange = *((NkMAIDRange*)pCapValue);

				freeByDataType(pCapValue, eDataType);
			}
			else
			{
				printf("No Info Present\n");
			}
			if (stRange.ulSteps == 0) {
				// the value of this capability is set to 'lfValue' directly
				printf("Input new value.\n>");
				scanf("%s", buf);
				stRange.lfValue = atof(buf);
			}
			else {
				// the value of this capability is calculated from 'ulValueIndex'
				lfValue = stRange.lfLower + stRange.ulValueIndex * (stRange.lfUpper - stRange.lfLower) / (stRange.ulSteps - 1);
				printf("Current Value: %f  (Max: %f  Min: %f)\n", lfValue, stRange.lfUpper, stRange.lfLower);
				printf("Input new value.\n>");
				scanf("%s", buf);
				lfValue = atof(buf);
				stRange.ulValueIndex = (ULONG)((lfValue - stRange.lfLower) * (stRange.ulSteps - 1) / (stRange.lfUpper - stRange.lfLower));
			}
			lerror = g_pMAIDSetCapability(kNkMAIDCapability_ExposureComp, &stRange, kNkMAIDDataType_RangePtr);
			PERROR(lerror);
		}
		break;
		case 11:// SaveMedia
			SetUnsignedIntCapability(kNkMAIDCapability_SaveMedia, pCapValue, eDataType);
			break;
		case 12:				//SDK:IT2:eNkMAIDMovieWBAutoType
			SetUnsignedIntCapability(kNkMAIDCapability_MovieWBAutoType, pCapValue, eDataType);
			break;
		case 14:
			SetEnumCapability(kNkMAIDCapability_MovieAperture, pCapValue, eDataType);
			break;
		case 15:
		{
			//kNkMAIDCapability_MovieExposureComp
			NkMAIDRange	stRange = { 0 };
			double lfValue;
			char buf[256];

			lerror = g_pMAIDGetCapability(kNkMAIDCapability_MovieExposureComp, kNkSDKGetSettingValue, pCapValue, eDataType);
			if (eDataType != kNkMAIDDataType_RangePtr)
			{
				printf("\nInvalid value returned \n");   freeByDataType(pCapValue, eDataType);
				break;
			}
			if (lerror == kNkMAIDResult_NoError && pCapValue != NULL)
			{
				stRange = *((NkMAIDRange*)pCapValue);

				freeByDataType(pCapValue, eDataType);

			}
			else
			{
				printf("No Info Present\n");
			}
			if (stRange.ulSteps == 0) {
				// the value of this capability is set to 'lfValue' directly
				printf("Input new value.\n>");
				scanf("%s", buf);
				stRange.lfValue = atof(buf);
			}
			else {
				// the value of this capability is calculated from 'ulValueIndex'
				lfValue = stRange.lfLower + stRange.ulValueIndex * (stRange.lfUpper - stRange.lfLower) / (stRange.ulSteps - 1);
				printf("Current Value: %f  (Max: %f  Min: %f)\n", lfValue, stRange.lfUpper, stRange.lfLower);
				printf("Input new value.\n>");
				scanf("%s", buf);
				lfValue = atof(buf);
				stRange.ulValueIndex = (ULONG)((lfValue - stRange.lfLower) * (stRange.ulSteps - 1) / (stRange.lfUpper - stRange.lfLower));
			}
			lerror = g_pMAIDSetCapability(kNkMAIDCapability_MovieExposureComp, &stRange, kNkMAIDDataType_RangePtr);
			PERROR(lerror);
		}
		break;
		case 19:
			SetUnsignedIntCapability(kNkMAIDCapability_LensType, pCapValue, eDataType);
			break;
		case 21:// ShutterSpeed(Exposure Time)
			SetEnumCapability(kNkMAIDCapability_MovieShutterSpeed, pCapValue, eDataType);
			break;
        case 24: //kNkMAIDCapability_EnableBracketing
            SetBoolCapability(kNkMAIDCapability_EnableBracketing, pCapValue, eDataType);
            break;
		case 25:// BracketingOrder
			SetEnumCapability(kNkMAIDCapability_BracketingOrder, pCapValue, eDataType);
			break;
		case 26:// AEBracketingStep
			SetEnumCapability(kNkMAIDCapability_AEBracketingStep, pCapValue, eDataType);
			break;
		case 27:// WBBracketingStep
			SetEnumCapability(kNkMAIDCapability_WBBracketingStep, pCapValue, eDataType);
			break;
		case 28:// BracketingType
			SetEnumCapability(kNkMAIDCapability_BracketingType, pCapValue, eDataType);
			break;
		case 29:// ADLBracketingType
			SetEnumCapability(kNkMAIDCapability_ADLBracketingType, pCapValue, eDataType);
			break;
		case 30:// ADLBracketingStep
			SetEnumCapability(kNkMAIDCapability_ADLBracketingStep, pCapValue, eDataType);
			break;
		case 31:// BracketingCount
			SetUnsignedIntCapability(kNkMAIDCapability_BracketingCount, pCapValue, eDataType);
			break;
		case 32: //kNkMAIDCapability_BracketingVary
			SetEnumCapability(kNkMAIDCapability_BracketingVary, pCapValue, eDataType);
			break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL SetUpCamera2()
{
	char	buf[256];
	UWORD	wSel;

	while (1)
	{
		printf("\nSelect the item you want to set up\n");
		printf(" 1. LockCamera			   2. LensInfo				 3. IsoControl\n");
		printf(" 4. ISOControlSensitivity	   5. MovieISOControl			 6. MovieSensitivity \n");
		printf(" 9. Active_D_Lighting             10. CCDDataMode	    	  	11. CompressionLevel\n");
		printf("13. CompressRAWEx		  14. PortraitImpressionBalance		15. FlashISOAutoHighLimit\n");
		printf("16. SkinSoftening		  17. FocalLength			18. FocusAreaMode\n");
		printf("19. FocusMode			  20. ToneMode				21. VibrationReduction\n");
		printf("22. Viewmode			  23. MeteringMode 			24. ISOAutoHiLimit\n");
		printf("25. ISOAutoShutterTime		  26. PictureControl			27. PictureControlHlg\n");
		printf("28. ChangeMonitorOffStatus	   0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:// LockCamera
			SetBoolCapability(kNkMAIDCapability_LockCamera, pCapValue, eDataType);
			break;

		case 2:// LensInfo
			SetStringCapability(kNkMAIDCapability_LensInfo, pCapValue, eDataType);
			break;

		case 3:// IsoControl 
			SetBoolCapability(kNkMAIDCapability_IsoControl, pCapValue, eDataType);
			break;

		case 4:
			SetEnumCapability(kNkMAIDCapability_ISOControlSensitivity, pCapValue, eDataType);
			break;

		case 5:
			SetBoolCapability(kNkMAIDCapability_MovieISOControl, pCapValue, eDataType);
			break;

		case 6:
			SetEnumCapability(kNkMAIDCapability_MovieSensitivity, pCapValue, eDataType);
			break;

		case 9:
			SetEnumCapability(kNkMAIDCapability_Active_D_Lighting, pCapValue, eDataType);
			break;

		case 10:// kNkMAIDCapability_CCDDataMode
			SetEnumCapability(kNkMAIDCapability_CCDDataMode, pCapValue, eDataType);
			break;

		case 11:// kNkMAIDCapability_CompressionLevel
			SetEnumCapability(kNkMAIDCapability_CompressionLevel, pCapValue, eDataType);
			break;

		case 13:// kNkMAIDCapability_CompressRAWEx
			SetEnumCapability(kNkMAIDCapability_CompressRAWEx, pCapValue, eDataType);
			break;

		case 14://kNkMAIDCapability_PortraitImpressionBalance
			SetEnumCapability(kNkMAIDCapability_PortraitImpressionBalance, pCapValue, eDataType);
			break;

		case 15:// kNkMAIDCapability_FlashISOAutoHighLimit
			SetEnumCapability(kNkMAIDCapability_FlashISOAutoHighLimit, pCapValue, eDataType);
			break;

		case 16://kNkMAIDCapability_SkinSoftening
			SetEnumCapability(kNkMAIDCapability_SkinSoftening, pCapValue, eDataType);
			break;

		case 17:// FocalLength
			SetRangeCapability(kNkMAIDCapability_FocalLength);
			break;

		case 18:// FocusAreaMode
			SetEnumCapability(kNkMAIDCapability_FocusAreaMode, pCapValue, eDataType);
			break;

		case 19: // kNkMAIDCapability_FocusMode
			SetEnumCapability(kNkMAIDCapability_FocusMode, pCapValue, eDataType);
			break;

		case 20:// kNkMAIDCapability_ToneMode
			SetUnsignedIntCapability(kNkMAIDCapability_ToneMode, pCapValue, eDataType);
			break;

		case 21:// kNkMAIDCapability_VibrationReduction
			SetEnumCapability(kNkMAIDCapability_VibrationReduction, pCapValue, eDataType);
			break;

		case 22: //Viewmode
			SetEnumCapability(kNkMAIDCapability_Viewmode, pCapValue, eDataType);
			break;

		case 23:// MeteringMode
			SetEnumCapability(kNkMAIDCapability_MeteringMode, pCapValue, eDataType);
			break;

		case 24:
			SetEnumCapability(kNkMAIDCapability_ISOAutoHiLimit, pCapValue, eDataType);
			break;

		case 25:// kNkMAIDCapability_ISOAutoShutterTime
			SetEnumCapability(kNkMAIDCapability_ISOAutoShutterTime, pCapValue, eDataType);
			break;

		case 26:// PictureControl
			SetEnumCapability(kNkMAIDCapability_PictureControl, pCapValue, eDataType);
			break;

		case 27:// kNkMAIDCapability_PictureControlHlg
			SetEnumCapability(kNkMAIDCapability_PictureControlHlg, pCapValue, eDataType);
			break;

		case 28:// kNkMAIDCapability_ChangeMonitorOffStatus
			SetEnumCapability(kNkMAIDCapability_ChangeMonitorOffStatus, pCapValue, eDataType);
			break;

		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL SetShootingMenu()
{
	char	buf[256];
	UWORD	wSel;

	while (1)
	{
		printf("\nSelect the item you want to set up\n");
		printf(" 1. WBMode			 2. Sensitivity			  3. WBFluorescentType\n");
		printf(" 4. WBAutoType			 5. WBTuneColorTempEx		  6. MovieWBMode \n");
		printf(" 7. MovieWBFluorescentType	 8. ShootingMode		  9. ContinuousShootingNum\n");
		printf("10. RemainContShooting		11. ShootingLimit		 12. RemainCountInMedia \n");
		printf("13. MovieWBTuneColorTempEx	14. WBTuneColorAdjust		 15. MovieWBTuneColorAdjust \n");
		printf("21. SpecialShootingMode         22. Slot2JpegImageSize		  0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{

		case 1:
			SetEnumCapability(kNkMAIDCapability_WBMode, pCapValue, eDataType);
			break;

		case 2:
			SetEnumCapability(kNkMAIDCapability_Sensitivity, pCapValue, eDataType);
			break;

		case 3:
			SetEnumCapability(kNkMAIDCapability_WBFluorescentType, pCapValue, eDataType);
			break;

		case 4:
			SetUnsignedIntCapability(kNkMAIDCapability_WBAutoType, pCapValue, eDataType);
			break;

		case 5:
			SetRangeCapability(kNkMAIDCapability_WBTuneColorTempEx);
			break;

		case 6:
			SetEnumCapability(kNkMAIDCapability_MovieWBMode, pCapValue, eDataType);
			break;

		case 7:
			SetEnumCapability(kNkMAIDCapability_MovieWBFluorescentType, pCapValue, eDataType);
			break;

		case 8:
			SetEnumCapability(kNkMAIDCapability_ShootingMode, pCapValue, eDataType);
			break;

		case 9:
			SetUnsignedIntCapability(kNkMAIDCapability_ContinuousShootingNum, pCapValue, eDataType);
			break;

		case 10:
			GetUnsignedIntCapability(kNkMAIDCapability_RemainContinuousShooting, pCapValue, eDataType);
			break;

		case 11:
			SetRangeCapability(kNkMAIDCapability_ShootingLimit);
			break;

		case 12:
			SetUnsignedIntCapability(kNkMAIDCapability_RemainCountInMedia, pCapValue, eDataType);
			break;

		case 13:
			SetRangeCapability(kNkMAIDCapability_MovieWBTuneColorTempEx);
			break;

		case 14:
			SetRangeCapability(kNkMAIDCapability_WBTuneColorAdjust);
			break;

		case 15:
			SetRangeCapability(kNkMAIDCapability_MovieWBTuneColorAdjust);
			break;

		case 21:
			SetEnumCapability(kNkMAIDCapability_SpecialShootingMode, pCapValue, eDataType);
			break;

		case 22:
			SetEnumCapability(kNkMAIDCapability_Slot2JpegImageSize, pCapValue, eDataType);
			break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}

	return true;
}

BOOL SetMovieMenu()
{
	char	buf[256];
	UWORD	wSel;
	bool	bRet;

	while (1)
	{
		printf("\nSelect the item you want to set up\n");
		printf(" 2. CountUpMethod\t\t  3. ExternalRecordingControl\n");
		printf(" 4. Active_D_Lighting\t\t  5. AfAreaMode\t\t\t  6. AFSubjectDetection\n");
		printf(" 7. Attenuator\t\t\t  8. CCDDataMode\t\t  9. FileType\n");
		printf("10. FocusMode\t\t\t 11. PictureControl\t\t 12. MovieSkinSoftening\n");
		printf("13. VibrationReduction\t\t 14. ISOAutoHiLimit\t\t 15. MeteringMode\n");
		printf("16. H265ToneMode\t\t 20. PortraitImpressionBalance\t 21. RecMicrophone\n");
		printf("22. RecMicrophoneValue\t\t 23. RecordingZone\t\t 24. ScreenSize\n");
		printf("25. ShutterMode\t\t\t 26. WindNoiseReduction\t\t  0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 2: //kNkMAIDCapability_CountUpMethod
			SetEnumCapability(kNkMAIDCapability_CountUpMethod, pCapValue, eDataType);
			break;

		case 3:// kNkMAIDCapability_ExternalRecordingControl
			SetEnumCapability(kNkMAIDCapability_ExternalRecordingControl, pCapValue, eDataType);
			break;

		case 4:// MovieActive_D_Lighting
			SetEnumCapability(kNkMAIDCapability_MovieActive_D_Lighting, pCapValue, eDataType);
			break;

		case 5:
			bRet = SetEnumCapability(kNkMAIDCapability_MovieAfAreaMode, pCapValue, eDataType);
			break;

		case 6:// kNkMAIDCapability_MovieAFSubjectDetection
			SetEnumCapability(kNkMAIDCapability_MovieAFSubjectDetection, pCapValue, eDataType);
			break;

		case 7:// MovieAttenuator
			SetEnumCapability(kNkMAIDCapability_MovieAttenuator, pCapValue, eDataType);
			break;

		case 8://kNkMAIDCapability_MovieCCDDataMode
			SetEnumCapability(kNkMAIDCapability_MovieCCDDataMode, pCapValue, eDataType);
			break;

		case 9:
			SetEnumCapability(kNkMAIDCapability_MovieFileType, pCapValue, eDataType);
			break;

		case 10:
			bRet = SetEnumCapability(kNkMAIDCapability_MovieFocusMode, pCapValue, eDataType);
			break;

		case 11:// kNkMAIDCapability_MoviePictureControl
			SetEnumCapability(kNkMAIDCapability_MoviePictureControl, pCapValue, eDataType);
			break;

		case 12://kNkMAIDCapability_MovieSkinSoftening
			SetEnumCapability(kNkMAIDCapability_MovieSkinSoftening, pCapValue, eDataType);
			break;

		case 13:// MovieVibrationReduction
			SetEnumCapability(kNkMAIDCapability_MovieVibrationReduction, pCapValue, eDataType);
			break;

		case 14:// kNkMAIDCapability_MovieISOAutoHiLimit
			SetEnumCapability(kNkMAIDCapability_MovieISOAutoHiLimit, pCapValue, eDataType);
			break;

		case 15:// MovieMeteringMode
			SetEnumCapability(kNkMAIDCapability_MovieMeteringMode, pCapValue, eDataType);
			break;

		case 16://kNkMAIDCapability_MovieH265ToneMode
			SetEnumCapability(kNkMAIDCapability_MovieH265ToneMode, pCapValue, eDataType);
			break;

		case 20://kNkMAIDCapability_MoviePortraitImpressionBalance
			SetEnumCapability(kNkMAIDCapability_MoviePortraitImpressionBalance, pCapValue, eDataType);
			break;

		case 21:
			SetUnsignedIntCapability(kNkMAIDCapability_MovieRecMicrophone, pCapValue, eDataType);
			break;

		case 22:
			SetRangeCapability(kNkMAIDCapability_MovieRecMicrophoneValue);
			break;

		case 23:
			SetUnsignedIntCapability(kNkMAIDCapability_MovieRecordingZone, pCapValue, eDataType);
			break;

		case 24://kNkMAIDCapability_MovieScreenSize
			SetEnumCapability(kNkMAIDCapability_MovieScreenSize, pCapValue, eDataType);
			break;

		case 25://kNkMAIDCapability_MovieShutterMode
			SetEnumCapability(kNkMAIDCapability_MovieShutterMode, pCapValue, eDataType);
			break;

		case 26://kNkMAIDCapability_MovieWindNoiseReduction
			SetUnsignedIntCapability(kNkMAIDCapability_MovieWindNoiseReduction, pCapValue, eDataType);
			break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL SetLiveView()
{
	char	buf[256];
	UWORD	wSel;

	while (1)
	{
		printf("\nSelect the item you want to set up\n");
		printf(" 1. LiveViewProhibit         2. LiveViewSelector\n");
		printf(" 0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{
		case 1:
			GetUnsignedIntCapability(kNkMAIDCapability_LiveViewProhibit, pCapValue, eDataType);
			break;

		case 2:
			SetEnumCapability(kNkMAIDCapability_LiveViewSelector, pCapValue, eDataType);
			break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}

BOOL SetSBMenu()
{
	char	buf[256];
	UWORD	wSel;
	bool	bRet;

	while (1)
	{
		printf("\nSelect the item you want to set up\n");
		printf(" 1. InternalFlashComp	0. Exit\n > ");

		scanf("%s", buf);
		wSel = atoi(buf);

		switch (wSel)
		{

		case 1: //kNkMAIDCapability_InternalFlashComp
			bRet = SetRangeCapability(kNkMAIDCapability_InternalFlashComp);
			break;
		}

		if (wSel == 0)
		{
			if (!strcmp(buf, "0"))
				break;
			else
				printf("\n Wrong Choice\n");
		}
	}
	return true;
}


