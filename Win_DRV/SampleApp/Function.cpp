//================================================================================================
// Copyright Nikon Corporation - All rights reserved
//
// View this file in a non-proportional font, tabs = 3
//================================================================================================
#include <io.h>
#include <mutex>
#include <windows.h>
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <math.h>
#include "CtrlSample.h"

#define CSLAYER

BOOL Load_Module(const char* Path)
{
	bool lib_check = false;

	g_hInstModule = LoadLibraryA((LPCSTR)Path);
	if (g_hInstModule == NULL)
	{
		g_hInstModule = LoadLibraryA((LPCSTR)"ControlServiceLayer.dll");
	}
	if (g_hInstModule) {
		lib_check = true;


		g_pMAIDEntryPoint = (LPMAIDEntryPointProc)GetProcAddress(g_hInstModule, "MAIDEntryPoint");
		if (g_pMAIDEntryPoint == NULL) {
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDInitializeSDK = (LPMAIDInitializeSDKProc)GetProcAddress(g_hInstModule, "InitializeSDK");
		if (g_pMAIDInitializeSDK == NULL) {
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDFreeSDK = (LPMAIDFreeSDKProc)GetProcAddress(g_hInstModule, "FreeSDK");
		if (g_pMAIDFreeSDK == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDConnectDevice = (LPMAIDConnectDeviceProc)GetProcAddress(g_hInstModule, "ConnectDevice");
		if (g_pMAIDConnectDevice == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDDisconnectDevice = (LPMAIDDisconnectDeviceProc)GetProcAddress(g_hInstModule, "DisconnectDevice");
		if (g_pMAIDDisconnectDevice == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDStartLiveView = (LPMAIDStartLiveView)GetProcAddress(g_hInstModule, "StartLiveView");
		if (g_pMAIDStartLiveView == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDStopLiveView = (LPMAIDStopLiveView)GetProcAddress(g_hInstModule, "StopLiveView");
		if (g_pMAIDStopLiveView == NULL) {
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDGetLiveViewStatus = (LPMAIDGetLiveViewStatus)GetProcAddress(g_hInstModule, "GetLiveViewStatus");
		if (g_pMAIDGetLiveViewStatus == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDGetLoggingLevel = (LPMAIDGetLoggingLevel)GetProcAddress(g_hInstModule, "GetLoggingLevel");
		if (g_pMAIDGetLoggingLevel == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDSetLoggingLevel = (LPMAIDSetLoggingLevel)GetProcAddress(g_hInstModule, "SetLoggingLevel");
		if (g_pMAIDSetLoggingLevel == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDStartShooting = (LPMAIDStartShooting)GetProcAddress(g_hInstModule, "StartShooting");
		if (g_pMAIDStartShooting == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDGetShootingStatus = (LPMAIDGetShootingStatus)GetProcAddress(g_hInstModule, "GetShootingStatus");
		if (g_pMAIDGetShootingStatus == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDGetRemainingShootCount = (LPMAIDGetRemainingShootCount)GetProcAddress(g_hInstModule, "GetRemainingShootCount");
		if (g_pMAIDGetRemainingShootCount == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDCancelShooting = (LPMAIDCancelShooting)GetProcAddress(g_hInstModule, "CancelShooting");
		if (g_pMAIDCancelShooting == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDGetCapability = (LPMAIDGetCapability)GetProcAddress(g_hInstModule, "GetCapability");
		if (g_pMAIDGetCapability == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDSetCapability = (LPMAIDSetCapability)GetProcAddress(g_hInstModule, "SetCapability");
		if (g_pMAIDSetCapability == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDEnumCapabilities = (LPMAIDEnumCapabilities)GetProcAddress(g_hInstModule, "EnumCapabilities");
		if (g_pMAIDEnumCapabilities == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDEnumDevices = (LPMAIDEnumDevices)GetProcAddress(g_hInstModule, "EnumDevices");
		if (g_pMAIDEnumDevices == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDStartMovieRecording = (LPMAIDStartMovieRecording)GetProcAddress(g_hInstModule, "StartMovieRecording");
		if (g_pMAIDStartMovieRecording == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDStopMovieRecording = (LPMAIDStopMovieRecording)GetProcAddress(g_hInstModule, "StopMovieRecording");
		if (g_pMAIDStopMovieRecording == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDStartOperation = (LPMAIDStartOperation)GetProcAddress(g_hInstModule, "StartOperation");
		if (g_pMAIDStartOperation == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}

		g_pMAIDSetImageVideoSavePath = (LPMAIDSetImageVideoSavePath)GetProcAddress(g_hInstModule, "SetImageVideoSavePath");
		if (g_pMAIDSetImageVideoSavePath == NULL)
		{
			puts("MAIDEntryPoint cannot be found.\n");
			lib_check = false;
		}
	}
	else {
		g_pMAIDEntryPoint = NULL;
		printf("\"%s\" cannot be opened.\n", (LPCSTR)Path);
	}

	if (lib_check == false)
		g_hInstModule = NULL;

	return (g_hInstModule != NULL) && (g_pMAIDEntryPoint != NULL);
}

void CALLPASCAL CALLBACK SrcEventProc(NKREF refProc, ULONG ulEvent, NKPARAM data)
{
	LPRefObj pRefParent = (LPRefObj)refProc, pRefChild = NULL;
	NkMAIDEventParam* pParam = NULL;

#ifdef CSLAYER
	NKERROR lError = kNkMAIDResult_NoError;
	LPNkMAIDDeviceInfo pDevInfo = NULL;
#endif

	switch (ulEvent) {
	case kNkMAIDEvent_AddChild:
		printf("kNkMAIDEvent_AddChild\n");
		break;
	case kNkMAIDEvent_RemoveChild:
		printf("kNkMAIDEvent_RemoveChild\n");
		break;
	case kNkMAIDEvent_WarmingUp:
		printf("kNkMAIDEvent_WarmingUp\n");
		break;
	case kNkMAIDEvent_WarmedUp:
		printf("kNkMAIDEvent_WarmedUp\n");
		// The Type0023 Module does not use this event.
		break;
	case kNkMAIDEvent_CapChange:
		if (data)
		{
			printf("kNkMAIDEvent_CapChange for %s received.\n", ((NkMAIDCapInfo*)data)->szDescription);
			m_capability_list_lock.lock();
			for (ULONG j = 0; j < pEnumCapInfo->ulCapCount; j++)
			{
				if (pEnumCapInfo->pCapArray[j].ulID == ((NkMAIDCapInfo*)data)->ulID)
				{
					pEnumCapInfo->pCapArray[j].ulOperations = ((NkMAIDCapInfo*)data)->ulOperations;
					pEnumCapInfo->pCapArray[j].ulType = ((NkMAIDCapInfo*)data)->ulType;
					pEnumCapInfo->pCapArray[j].ulVisibility = ((NkMAIDCapInfo*)data)->ulVisibility;
					break;
				}
			}
			m_capability_list_lock.unlock();
			free(((NkMAIDCapInfo*)data));
		}
		else
		{
			printf("kNkMAIDEvent_CapChange received with null data");
		}

		break;
	case kNkMAIDEvent_CapChangeOperationOnly:
		if (data)
		{
			printf("kNkMAIDEvent_CapChangeOperationOnly for %s received.\n", ((NkMAIDCapInfo*)data)->szDescription);
			m_capability_list_lock.lock();
			for (ULONG j = 0; j < pEnumCapInfo->ulCapCount; j++)
			{
				if (pEnumCapInfo->pCapArray[j].ulID == ((NkMAIDCapInfo*)data)->ulID)
				{
					pEnumCapInfo->pCapArray[j].ulOperations = ((NkMAIDCapInfo*)data)->ulOperations;
					break;
				}
			}
			m_capability_list_lock.unlock();
			free(((NkMAIDCapInfo*)data));
		}
		else
		{
			printf("kNkMAIDEvent_CapChangeOperationOnly received with null data");
		}
		break;
	case kNkMAIDEvent_CapChangeValueOnly:
        printf("The value of Capability(CapID=0x%X) was changed.\n", (ULONG)data);
		break;
	case kNkMAIDEvent_OrphanedChildren:
		printf("kNkMAIDEvent_OrphanedChildren\n");
		break;
	case kNkMAIDEvent_AddPreviewImage:
		puts("Event_AddPreviewImage to Item object is not supported.\n");
		break;
	case kNkMAIDEvent_CaptureComplete:
		puts("\nkNkMAIDEvent_CaptureComplete event.\n");
		break;
	case kNkMAIDEvent_AddChildInCard:
		printf("a Video object(ID=0x%X) added in card.\n", (ULONG)data);
		break;
	case kNkMAIDEvent_RecordingInterrupted:
		printf("Recording was Interrupted\n");
		break;
	case kNkMAIDEvent_SBAdded:
		printf("SB Added\n ");
		break;
	case kNkMAIDEvent_SBRemoved:
		printf("kNkMAIDEvent_SBRemoved\n");
		break;
	case kNkMAIDEvent_SBAttrChanged:
		printf("kNkMAIDEvent_SBAttrChanged\n");
		break;
	case kNkMAIDEvent_SBGroupAttrChanged:
		printf("kNkMAIDEvent_SBGroupAttrChanged\n");
		break;
	case kNkMAIDEvent_MovieRecordComplete:
	{
		char strParam[64] = "";
		switch ((ULONG)data) {
		case 0:
			strcpy(strParam, "Card Recording");
			break;
		case 1:
			strcpy(strParam, "ExternalDevice Recording");
			break;
		case 2:
			strcpy(strParam, "Card and ExternalDevice Recording");
			break;
		default:
			strcpy(strParam, "Unknown parameter");
			break;
		}
		printf("MovieRecordComplete Event(%s)\r\n", strParam);
		break;
	}
	case kNkMAIDEvent_ManualSettingLensDataChanged:
	{
		char strParam[64] = "";
		if (((ULONG)data) <= 19) {
			sprintf(strParam, "No.%d", (((int)data) + 1));
		}
		else {
			sprintf(strParam, "Unknown parameter");
		}
		printf("ManualSettingLensData Changed(%s)\r\n", strParam);
		break;
	}
	case kNkMAIDEvent_PictureControlAdjustChanged:
		printf("kNkMAIDEvent_PictureControlAdjustChanged\n");
		break;
	case kNkMAIDEvent_StartMovieRecord:
	{
		char strParam[64] = "";
		switch ((ULONG)data) {
		case 0:
			strcpy(strParam, "Recording to Card");
			break;
		case 1:
			strcpy(strParam, "Recording to External Recording Device");
			break;
		case 2:
			strcpy(strParam, "Recording to Card and External Recording Device");
			break;
		default:
			strcpy(strParam, "Unknown parameter");
			break;
		}
		printf("MovieRecordComplete Event(%s)\r\n", strParam);
		break;
	}

#ifdef CSLAYER
	case kNkMAIDEvent_DeviceInfoChanged:
		printf("Device Info changed (Data = 0x%X).\n", (ULONG)data);

		device_list_lock.lock();

		if (pDeviceList)
		{
			if (pDeviceList->pDeviceData)
				free(pDeviceList->pDeviceData);
			free(pDeviceList);
			pDeviceList = NULL;
		}

		lError = g_pMAIDEnumDevices(pDeviceList, NULL, NULL);
		if (lError != kNkMAIDResult_NoError || pDeviceList == NULL ||
			pDeviceList->ulElements == 0 || pDeviceList->pDeviceData == NULL)
		{
			device_list_lock.unlock();
			return;
		}
		pDevInfo = pDeviceList->pDeviceData;
		for (ULONG i = 0; i < pDeviceList->ulElements; i++)
		{
			printf("Index = %d, Device Id = %d, Device Name = %s, Available = %s\n",
				i + 1, pDeviceList->pDeviceData[i].ID, pDeviceList->pDeviceData[i].Name,
				(pDeviceList->pDeviceData[i].Availability ? "True" : "False"));
		}

		device_list_lock.unlock();
		break;

	case kNkMAIDEvent_MirrorUpCancelComplete:
		std::cout << "Received kNkMAIDEvent_MirrorUpCancelComplete" << std::endl;
		break;
	case kNkMAIDEvent_ImageSavedInCard:
		std::cout << "Received kNkMAIDEvent_ImageSavedInCard" << std::endl;
		break;
	case kNkMAIDEvent_ImageSaved:
#ifdef _WIN32
		wprintf(L"kNkMAIDEvent_ImageSaved event received %s", (data ? (wchar_t*)data : L""));
#else
		printf("kNkMAIDEvent_ImageSaved event received %s", (data ? data : ""));
#endif
		free((void*)data);
		break;
#endif

	case kNkMAIDEvent_StorageFull_ImageNotSaved:
		std::cout << "Received kNkMAIDEvent_StorageFull_ImageNotSaved" << std::endl;
		break;

	case kNkMAIDEvent_AcquireFailed_ImageNotSaved:
		std::cout << "Received kNkMAIDEvent_AcquireFailed_ImageNotSaved" << std::endl;
		break;

	case kNkMAIDEvent_1stCaptureComplete:
		std::cout << "Received kNkMAIDEvent_1stCaptureComplete" << std::endl;
		break;

	case kNkMAIDEvent_OpenCaptureComplete:
		puts("\nkNkMAIDEvent_OpenCaptureComplete event.\n");
		break;

	case kNkMAIDEvent_CaptureSkip:
		puts("\nkNkMAIDEvent_CaptureSkip event.\n");
		break;

	case kNkMAIDEvent_LiveViewStateChanged:
		puts("\nkNkMAIDEvent_LiveViewStateChanged event.\n");
		break;

	case kNkMAIDEvent_PixelMappingComplete:
		puts("\nkNkMAIDEvent_PixelMappingComplete event.\n");
		break;

	case kNkMAIDEvent_HlgQualityAdjustChanged:
		puts("\nkNkMAIDEvent_HlgQualityAdjustChanged event.\n");
		break;

	case kNkMAIDEvent_PortraitImpressionBalanceAdjustChanged:
		puts("\nkNkMAIDEvent_PortraitImpressionBalanceAdjustChanged event.\n");
		break;

	case kNkMAIDEvent_PictureControlHlgAdjustChanged:
		puts("\nkNkMAIDEvent_PictureControlHlgAdjustChanged event.\n");
		break;

	case kNkMAIDEvent_AddImageInCard:
		std::cout << "Received kNkMAIDEvent_AddImageInCard" << std::endl;
		break;

	case kNkMAIDEvent_FocusShiftShootingStarted:
		std::cout << "Received kNkMAIDEvent_FocusShiftShootingStarted" << std::endl;
		break;

	case kNkMAIDEvent_FocusShiftShootingStopped:
		std::cout << "Received kNkMAIDEvent_FocusShiftShootingStopped" << std::endl;
		break;

	case kNkMAIDEvent_PixelShiftShootingStarted:
		std::cout << "Received kNkMAIDEvent_PixelShiftShootingStarted" << std::endl;
		break;

	case kNkMAIDEvent_PixelShiftShootingStopped:
		std::cout << "Received kNkMAIDEvent_PixelShiftShootingStopped" << std::endl;
		break;

	case kNkMAIDEvent_ChangeSaveDestination:
		std::cout << "Received kNkMAIDEvent_ChangeSaveDestination" << std::endl;
		break;

	default:
		puts("Detected unknown Event to the Source object.\n");
	}
}

ULONG CALLPASCAL CALLBACK UIRequestProc(NKREF ref, LPNkMAIDUIRequestInfo pUIRequest)
{
	short	 nRet = kNkMAIDUIRequestResult_None;
	char	sAns[256];

	// display message
	if (pUIRequest->lpPrompt)
		printf("\n%s\n", pUIRequest->lpPrompt);
	if (pUIRequest->lpDetail)
		printf("\n%s\n", pUIRequest->lpDetail);

	// get an answer
	switch (pUIRequest->ulType) {
	case kNkMAIDUIRequestType_Ok:
		do {
			printf("\nPress 'O' key. ('O': OK)\n>");
			scanf("%s", sAns);
		} while (*sAns != 'o' && *sAns != 'O');
		nRet = kNkMAIDUIRequestResult_Ok;
		break;
	case kNkMAIDUIRequestType_OkCancel:
		do {
			printf("\nPress 'O' or 'C' key. ('O': OK   'C': Cancel)\n>");
			scanf("%s", sAns);
		} while (*sAns != 'o' && *sAns != 'O' && *sAns != 'c' && *sAns != 'C');
		if (*sAns == 'o' || *sAns == 'O')
			nRet = kNkMAIDUIRequestResult_Ok;
		else if (*sAns == 'c' || *sAns == 'C')
			nRet = kNkMAIDUIRequestResult_Cancel;
		break;
	case kNkMAIDUIRequestType_YesNo:
		do {
			printf("\nPress 'Y' or 'N' key. ('Y': Yes   'N': No)\n>");
			scanf("%s", sAns);
		} while (*sAns != 'y' && *sAns != 'Y' && *sAns != 'n' && *sAns != 'N');
		if (*sAns == 'y' || *sAns == 'Y')
			nRet = kNkMAIDUIRequestResult_Yes;
		else if (*sAns == 'n' || *sAns == 'N')
			nRet = kNkMAIDUIRequestResult_No;
		break;
	case kNkMAIDUIRequestType_YesNoCancel:
		do {
			printf("\nPress 'Y' or 'N' or 'C' key. ('Y': Yes   'N': No   'C': Cancel)\n>");
			scanf("%s", sAns);
		} while (*sAns != 'y' && *sAns != 'Y' && *sAns != 'n' && *sAns != 'N' && *sAns != 'c' && *sAns != 'C');
		if (*sAns == 'y' || *sAns == 'Y')
			nRet = kNkMAIDUIRequestResult_Yes;
		else if (*sAns == 'n' || *sAns == 'N')
			nRet = kNkMAIDUIRequestResult_No;
		else if (*sAns == 'c' || *sAns == 'C')
			nRet = kNkMAIDUIRequestResult_Cancel;
		break;
	default:
		nRet = kNkMAIDUIRequestResult_None;
	}

	return nRet;
}

void CALLPASCAL CALLBACK ProgressProc(
	ULONG				ulCommand,			// Command, one of eNkMAIDCommand
	ULONG				ulParam,				// parameter for the command
	NKREF				refProc,				// Reference set by client
	ULONG				ulDone,				// Numerator
	ULONG				ulTotal)			// Denominator
{
#ifdef PERFORMANCECHECK
	static std::chrono::time_point<std::chrono::system_clock> time_point1, time_point2;
	static bool b_flg = FALSE;
	if ((ulDone == 0) || (b_flg == FALSE))
	{
		time_point1 = std::chrono::system_clock::now();
		b_flg = TRUE;
	}
#endif
	printf("Done - %ul   Total - %ul\n", ulDone, ulTotal);
#ifdef PERFORMANCECHECK
	if (ulDone >= ulTotal)
	{
		time_point2 = std::chrono::system_clock::now();
		auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(time_point2 - time_point1).count();
		std::cout << "\n Progress Duration: " << duration << "\n";
		b_flg = FALSE;
	}
#endif
}

NKERROR CALLPASCAL CALLBACK DataProc(NKREF ref, LPVOID pInfo, LPVOID pData)
{
	if (pInfo && pData)
	{
		LPNkMAIDFileInfo pFileInfo = (LPNkMAIDFileInfo)pInfo;
		CreateDirectoryA("preview", NULL);
		if (pFileInfo->fDiskFile)
		{
			printf("\n[SDK] Image saved on disk: %s\n", (char*)pData);
		}
		else
		{
			const char* mode = (pFileInfo->ulStart == 0) ? "wb" : "ab";
			FILE* fp = fopen("preview/last_shot.jpg", mode);
			if (fp)
			{
				fwrite(pData, 1, pFileInfo->ulLength, fp);
				fclose(fp);
			}
			printf("\n[SDK] Image data chunk: %u/%u bytes\n", pFileInfo->ulStart + pFileInfo->ulLength, pFileInfo->ulTotalLength);
		}
	}
	return kNkMAIDResult_NoError;
}

NKERROR CALLPASCAL CALLBACK LVDataProc(NKREF refProc, LPNkMAIDLiveViewData pstLiveViewData)
{
	if (pstLiveViewData == NULL || pstLiveViewData->ulLvImageSize == 0 || pstLiveViewData->pImageData == NULL)
	{
		return kNkMAIDResult_NoError;
	}

	CreateDirectoryA("preview", NULL);
	FILE* hPreview = fopen("preview/last_preview.jpg", "wb");
	if (hPreview != NULL)
	{
		fwrite(pstLiveViewData->pImageData, 1, pstLiveViewData->ulLvImageSize, hPreview);
		fclose(hPreview);
	}

	if (pstLiveViewData)
	{
		if (pstLiveViewData->pImageData) free(pstLiveViewData->pImageData);
		free(pstLiveViewData);
		pstLiveViewData = NULL;
	}

	return kNkMAIDResult_NoError;
}

void* _stdcall AllocateMemory(size_t len)
{
	return malloc(len);
}

void _stdcall FreeMemory(void* pMem)
{
	free(pMem);
}

void CompProc(NKREF refComplete, NKERROR nResult)
{
	*((ULONG*)refComplete) = nResult;
	printf("Inside completetion proc Res = %d\n", nResult);
}

BOOL  CheckCapability(ULONG ulCapID, eNkMAIDCapOperations operationDesc)
{
	ULONG j = 0;

	m_capability_list_lock.lock();

	for (j = 0; j < pEnumCapInfo->ulCapCount; j++)
	{
		if (pEnumCapInfo->pCapArray[j].ulID == ulCapID)
			break;
	}

	if (j == pEnumCapInfo->ulCapCount)
	{
		m_capability_list_lock.unlock();
		printf("Capability is not present in this camera model\n");
		return FALSE;
	}

	if (!(pEnumCapInfo->pCapArray[j].ulOperations & operationDesc))
	{
		switch (operationDesc)
		{
		case kNkMAIDCapOperation_Get:
			printf("Capability Get operation not allowed\n");
			break;

		case kNkMAIDCapOperation_Set:
			printf("Capability Set operation not allowed\n");
			break;

		case kNkMAIDCapOperation_GetArray:
			printf("Capability GetArray operation not allowed\n");
			break;

		case kNkMAIDCapOperation_Start:
			printf("Capability Start  operation not allowed\n");
			break;

		default:
			printf("Capability GetDefault operation not allowed\n");
			break;
		}

		m_capability_list_lock.unlock();
		return FALSE;
	}

	m_capability_list_lock.unlock();
	return TRUE;
}

BOOL GetCapabilityType(ULONG ulCapID, ULONG& pCapType)
{
	ULONG j = 0;

	m_capability_list_lock.lock();

	for (j = 0; j < pEnumCapInfo->ulCapCount; j++)
	{
		if (pEnumCapInfo->pCapArray[j].ulID == ulCapID)
			break;
	}

	if (j == pEnumCapInfo->ulCapCount)
	{
		printf("capability not found\n");
		m_capability_list_lock.unlock();
		return FALSE;
	}

	pCapType = pEnumCapInfo->pCapArray[j].ulType;
	m_capability_list_lock.unlock();
	return TRUE;
}

void    SetUnsignedString(ULONG ulCapID)
{
	switch (ulCapID)
	{
	case kNkMAIDCapability_MeteringMode:
		printf("1 kNkMAIDMeteringMode_Matrix \n");
		printf("2 kNkMAIDMeteringMode_CenterWeighted \n");
		printf("3 kNkMAIDMeteringMode_Spot\n");
		printf("4 kNkMAIDMeteringMode_HighLight\n");
		break;
	case kNkMAIDCapability_FocusMode:
		printf("1 kNkMAIDFocusMode_MF\n");
		printf("2 kNkMAIDFocusMode_AFs\n");
		printf("3 kNkMAIDFocusMode_AFc\n");
		printf("4 kNkMAIDFocusMode_AFf\n");
		break;
	case kNkMAIDCapability_RawJpegImageStatus:
		printf("1  eNkMAIDRawJpegImageStatus_Single\n");
		printf("2 eNkMAIDRawJpegImageStatus_RawJpeg\n");
		break;
	case kNkMAIDCapability_DataTypes:
		printf("1 kNkMAIDDataObjType_Image");
		printf("2 kNkMAIDDataObjType_Sound");
		printf("3 kNkMAIDDataObjType_Video");
		printf("4 kNkMAIDDataObjType_Thumbnail");
		printf("5 kNkMAIDDataObjType_File");
		break;
	case kNkMAIDCapability_ModuleType:
		printf("1 kNkMAIDModuleType_Scanner\n");
		printf("2 kNkMAIDModuleType_Camera\n");
		break;
	case kNkMAIDCapability_WBFluorescentType:
		printf("1  kNkWBFluorescentType_SodiumVapor\n");
		printf("2 kNkWBFluorescentType_WarmWhite\n");
		printf("3 kNkWBFluorescentType_White\n");
		printf("4 kNkWBFluorescentType_CoolWhite\n");
		printf("5 kNkWBFluorescentType_DayWhite\n");
		printf("6 kNkWBFluorescentType_Daylight\n");
		printf("7 kNkWBFluorescentType_HiTempMercuryVapor\n");
		break;
	case kNkMAIDCapability_LiveViewProhibit:
		printf("1 kNkMAIDLiveViewProhibit_Retractable \n");
		printf("2 kNkMAIDLiveViewProhibit_DuringMirrorup \n");
		printf("3 kNkMAIDLiveViewProhibit_BulbWarning \n");
		printf("4 kNkMAIDLiveViewProhibit_TempRise\n");
		printf("5 kNkMAIDLiveViewProhibit_Capture\n");
		printf("6 kNkMAIDLiveViewProhibit_NoCardLock\n");
		printf("7 kNkMAIDLiveViewProhibit_SdramImg\n");
		printf("8 kNkMAIDLiveViewProhibit_TTL\n");
		printf("9 kNkMAIDLiveViewProhibit_Battery\n");
		printf("10 kNkMAIDLiveViewProhibit_FEE\n");
		printf("11 kNkMAIDLiveViewProhibit_Sequence\n");
		break;
	case kNkMAIDCapability_LiveViewStatus:
		printf("1 kNkMAIDLiveViewStatus_OFF\n");
		printf("2 kNkMAIDLiveViewStatus_ON\n");
		break;
	case kNkMAIDCapability_MovRecInCardStatus:
		printf("1 kNkMAIDMovRecInCardStatus_Off\n");
		printf("2 kNkMAIDMovRecInCardStatus_On\n");
		break;
	case kNkMAIDCapability_MovRecInCardProhibit:
		printf("1 kNkMAIDMovRecInCardProhibit_LVPhoto\n");
		printf("2 kNkMAIDMovRecInCardProhibit_LVImageZoom\n");
		printf("3 kNkMAIDMovRecInCardProhibit_RecMov\n");
		printf("4 kNkMAIDMovRecInCardProhibit_MovInBuf\n");
		printf("5 kNkMAIDMovRecInCardProhibit_CardFull\n");
		printf("6 kNkMAIDMovRecInCardProhibit_NoFormat\n");
		printf("7 kNkMAIDMovRecInCardProhibit_CardErr\n");
		printf("8 kNkMAIDMovRecInCardProhibit_NoCard\n");
		break;
	case kNkMAIDCapability_SaveMedia:
		printf("1 kNkMAIDSaveMedia_Card\n");
		printf("2 kNkMAIDSaveMedia_SDRAM\n");
		printf("3 kNkMAIDSaveMedia_Card_SDRAM\n");
		break;
	case kNkMAIDCapability_AFMode:
		printf("1 kNkMAIDAFMode_S\n");
		printf("2 kNkMAIDAFMode_C\n");
		printf("3 kNkMAIDAFMode_M_FIX\n");
		printf("4 kNkMAIDAFMode_M_SEL\n");
		break;
	case kNkMAIDCapability_MirrorUpStatus:
		printf("1 kNkMAIDMirrorUpStatus_Down\n");
		printf("2 kNkMAIDMirrorUpStatus_Up\n");
		break;
	case kNkMAIDCapability_MovieMeteringMode:
		printf("1 kNkMAIDMovieMeteringMode_Matrix\n");
		printf("2 kNkMAIDMovieMeteringMode_CenterWeighted\n");
		printf("3 kNkMAIDMovieMeteringMode_HighLight\n");
		break;
	case kNkMAIDCapability_IPTCPresetSelect:
		printf("1 kNkMAIDIPTCPresetSelect_OFF\n");
		printf("PresetSelect1 - 10\n");
		break;
	case kNkMAIDCapability_AFLockOnAcross:
		printf("1(Quick) - 5(Slow)\n");
		break;
	case kNkMAIDCapability_AFLockOnMove:
		printf("1(Steady) - 3(Erratic)\n");
		break;
	case kNkMAIDCapability_FaceDetection:
		printf("1 kNkMAIDFaceDetection_Off\n");
		printf("2 kNkMAIDFaceDetection_On\n");
		break;
	case kNkMAIDCapability_MatrixMetering:
		printf("1 kNkMAIDMatrixMetering_Off\n");
		printf("2 kNkMAIDMatrixMetering_On\n");
		break;
	case kNkMAIDCapability_ExposureCompFlashUsed:
		printf("1 kNkMAIDExposureCompFlashUsed_Entireframe\n");
		printf("2 kNkMAIDExposureCompFlashUsed_Backgroundonly\n");
		break;
	case kNkMAIDCapability_ElectronicFrontCurtainShutter:
		printf("1 kNkMAIDElectronicFrontCurtainShutter_Off\n");
		printf("2 kNkMAIDElectronicFrontCurtainShutter_On\n");
		break;
	case kNkMAIDCapability_GetIPTCInfo:
		printf("1 kNkMAIDGetIPTCInfo_None\n");
		printf("2 kNkMAIDGetIPTCInfo_Attached\n");
		break;
	case kNkMAIDCapability_MFDrive:
		printf("%d : InfinityToClosest\n", kNkMAIDMFDrive_InfinityToClosest);
		printf("%d : ClosestToInfinity\n", kNkMAIDMFDrive_ClosestToInfinity);
		break;
	case kNkMAIDCapability_AllTestFiringDisable:
		printf("1 kNkMAIDAllTestFiringDisable_Enable\n");
		printf("2 kNkMAIDAllTestFiringDisable_Disable\n");
		break;
	case kNkMAIDCapability_RadioMultipleFlashChannel:
		printf("1 kNkMAIDRadioMultipleFlashChannel_Unknown\n");
		printf("2 kNkMAIDRadioMultipleFlashChannel_5ch\n");
		printf("3 kNkMAIDRadioMultipleFlashChannel_10ch\n");
		printf("4 kNkMAIDRadioMultipleFlashChannel_15ch\n");
		break;
	case kNkMAIDCapability_FlickerReductionSetting:
		printf("1 kNkMAIDFlickerReductionSetting_Off\n");
		printf("2 kNkMAIDFlickerReductionSetting_On\n");
		break;
	case kNkMAIDCapability_MovieActive_D_Lighting:
		printf("1 kNkMAIDMovieActive_D_Lighting_Off\n");
		printf("2 kNkMAIDMovieActive_D_Lighting_Low\n");
		printf("3 kNkMAIDMovieActive_D_Lighting_Normal\n");
		printf("4 kNkMAIDMovieActive_D_Lighting_High\n");
		printf("5 kNkMAIDMovieActive_D_Lighting_ExtraHigh\n");
		printf("6 kNkMAIDMovieActive_D_Lighting_SamePhoto\n");
		break;
	case kNkMAIDCapability_ElectronicVR:
		printf("1 kMAIDElectronicVR_OFF\n");
		printf("2 kMAIDElectronicVR_ON\n");
		break;
	default:
		break;
	}
}

char* GetUnsignedString(ULONG ulCapID, ULONG ulValue, char* psString)
{
	char buff[2048];

	switch (ulCapID)
	{
	case kNkMAIDCapability_MovieWindNoiseReduction:
		strcpy(psString, "0 - OFF\n");
		sprintf(buff, "1 - ON\n");
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ToneMode:
		sprintf(buff, "%d : SDR\n", kNkMAIDToneMode_SDR);
		strcpy(psString, buff);
		sprintf(buff, "%d : HLG\n", kNkMAIDToneMode_HLG);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ChangeMonitorOffStatus:
		sprintf(buff, "%d : CancelForcedTurnOff\n", kNkMAIDChangeMonitorOffStatus_CancelForcedTurnOff);
		strcpy(psString, buff);
		sprintf(buff, "%d : ForcedTurnOff\n", kNkMAIDChangeMonitorOffStatus_ForcedTurnOff);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_VibrationReduction:
		sprintf(buff, "%d : Off\n", kNkMAIDVibrationReduction_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : Normal\n", kNkMAIDVibrationReduction_Normal);
		strcat(psString, buff);
		sprintf(buff, "%d : Sport\n", kNkMAIDVibrationReduction_Sport);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_HighlightBrightness:
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_180\n", kNkMAIDHighlightBrightness_180);
		strcpy(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_191\n", kNkMAIDHighlightBrightness_191);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_202\n", kNkMAIDHighlightBrightness_202);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_213\n", kNkMAIDHighlightBrightness_213);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_224\n", kNkMAIDHighlightBrightness_224);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_235\n", kNkMAIDHighlightBrightness_235);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_248\n", kNkMAIDHighlightBrightness_248);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_255\n", kNkMAIDHighlightBrightness_255);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_120\n", kNkMAIDHighlightBrightness_120);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_125\n", kNkMAIDHighlightBrightness_125);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_130\n", kNkMAIDHighlightBrightness_130);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_135\n", kNkMAIDHighlightBrightness_135);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_140\n", kNkMAIDHighlightBrightness_140);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_145\n", kNkMAIDHighlightBrightness_145);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_150\n", kNkMAIDHighlightBrightness_150);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_155\n", kNkMAIDHighlightBrightness_155);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_160\n", kNkMAIDHighlightBrightness_160);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_165\n", kNkMAIDHighlightBrightness_165);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_170\n", kNkMAIDHighlightBrightness_170);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_175\n", kNkMAIDHighlightBrightness_175);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_185\n", kNkMAIDHighlightBrightness_185);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_190\n", kNkMAIDHighlightBrightness_190);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_195\n", kNkMAIDHighlightBrightness_195);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_200\n", kNkMAIDHighlightBrightness_200);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_205\n", kNkMAIDHighlightBrightness_205);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_210\n", kNkMAIDHighlightBrightness_210);
		strcat(psString, buff);
		sprintf(buff, "%d :kNkMAIDHighlightBrightness_215\n", kNkMAIDHighlightBrightness_215);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_220\n", kNkMAIDHighlightBrightness_220);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_225\n", kNkMAIDHighlightBrightness_225);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_230\n", kNkMAIDHighlightBrightness_230);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_240\n", kNkMAIDHighlightBrightness_240);
		strcat(psString, buff);
		sprintf(buff, "%d :kNkMAIDHighlightBrightness_245\n", kNkMAIDHighlightBrightness_245);
		strcat(psString, buff);
		sprintf(buff, "%d : kNkMAIDHighlightBrightness_250\n", kNkMAIDHighlightBrightness_250);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ExternalRecordingControl:
		sprintf(buff, "%d : Off\n", kNkMAIDExternalRecordingControl_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : On\n", kNkMAIDExternalRecordingControl_On);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ActiveSlot:
		sprintf(buff, "%d : NoCard\n", kNkMAIDActiveSlot_NoCard);
		strcpy(psString, buff);
		sprintf(buff, "%d : Slot1\n", kNkMAIDActiveSlot_Slot1);
		strcat(psString, buff);
		sprintf(buff, "%d : Slot2\n", kNkMAIDActiveSlot_Slot2);
		strcat(psString, buff);
		sprintf(buff, "%d : Slot1_Slot2\n", kNkMAIDActiveSlot_Slot1_Slot2);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_CompressRAWBitMode:
		sprintf(buff, "%d : 12bit\n", kNkMAIDCompressRAWBitMode_12bit);
		strcpy(psString, buff);
		sprintf(buff, "%d : 14bit\n", kNkMAIDCompressRAWBitMode_14bit);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_EffectMode:
		sprintf(buff, "%d : NightVision\n", kNkMAIDEffectMode_NightVision);
		strcpy(psString, buff);
		sprintf(buff, "%d : ColorSketch\n", kNkMAIDEffectMode_ColorSketch);
		strcat(psString, buff);
		sprintf(buff, "%d : Miniature\n", kNkMAIDEffectMode_Miniature);
		strcat(psString, buff);
		sprintf(buff, "%d : SelectColor\n", kNkMAIDEffectMode_SelectColor);
		strcat(psString, buff);
		sprintf(buff, "%d : Silhouette\n", kNkMAIDEffectMode_Silhouette);
		strcat(psString, buff);
		sprintf(buff, "%d : Highkey\n", kNkMAIDEffectMode_Highkey);
		strcat(psString, buff);
		sprintf(buff, "%d : Lowkey\n", kNkMAIDEffectMode_Lowkey);
		strcat(psString, buff);
		sprintf(buff, "%d : ToyCamera\n", kNkMAIDEffectMode_ToyCamera);
		strcat(psString, buff);
		sprintf(buff, "%d : HDRPainting\n", kNkMAIDEffectMode_HDRPainting);
		strcat(psString, buff);
		sprintf(buff, "%d : SuperVivid\n", kNkMAIDEffectMode_SuperVivid);
		strcat(psString, buff);
		sprintf(buff, "%d : Pop\n", kNkMAIDEffectMode_Pop);
		strcat(psString, buff);
		sprintf(buff, "%d : PhotoIllustration\n", kNkMAIDEffectMode_PhotoIllustration);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_BlinkingStatus:
		sprintf(buff, "%d : Both a shutter speed and an aperture are displayed with normal status\n", kNkMAIDBlinkingStatus_None);
		strcpy(psString, buff);
		sprintf(buff, "%d : Only a shutter speed is displayed with blinking status.\n", kNkMAIDBlinkingStatus_Sp_Blink);
		strcat(psString, buff);
		sprintf(buff, "%d : Only an aperture is displayed with blinking status.\n", kNkMAIDBlinkingStatus_Ap_Blink);
		strcat(psString, buff);
		sprintf(buff, "%d : Both a shutter speed and an aperture are displayed with blinking status.\n", kNkMAIDBlinkingStatus_Both);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_CameraInclination:
		sprintf(buff, "%d : Horizontal or Unsettled\n", eNkMAIDCameraInclination_Level);
		strcpy(psString, buff);
		sprintf(buff, "%d : Vertical(Grip is top)\n", eNkMAIDCameraInclination_GripTop);
		strcat(psString, buff);
		sprintf(buff, "%d : Vertical(Grip is bottom)\n", eNkMAIDCameraInclination_GripBottom);
		strcat(psString, buff);
		sprintf(buff, "%d : Horizontal(Up Down)\n", eNkMAIDCameraInclination_LevelUpDown);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MeteringMode:
		sprintf(buff, "%d : Matrix\n", kNkMAIDMeteringMode_Matrix);
		strcpy(psString, buff);
		sprintf(buff, "%d : CenterWeighted\n", kNkMAIDMeteringMode_CenterWeighted);
		strcat(psString, buff);
		sprintf(buff, "%d : Spot\n", kNkMAIDMeteringMode_Spot);
		strcat(psString, buff);
		sprintf(buff, "%d : HighLight\n", kNkMAIDMeteringMode_HighLight);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_FocusMode:
		sprintf(buff, "%d : MF\n", kNkMAIDFocusMode_MF);
		strcpy(psString, buff);
		sprintf(buff, "%d : AF-S\n", kNkMAIDFocusMode_AFs);
		strcat(psString, buff);
		sprintf(buff, "%d : AF-C\n", kNkMAIDFocusMode_AFc);
		strcat(psString, buff);
		sprintf(buff, "%d : AF-F\n", kNkMAIDFocusMode_AFf);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_RawJpegImageStatus:
		sprintf(buff, "%d : Single\n", eNkMAIDRawJpegImageStatus_Single);
		strcpy(psString, buff);
		sprintf(buff, "%d : Raw + Jpeg\n", eNkMAIDRawJpegImageStatus_RawJpeg);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_DataTypes:
		strcpy(psString, "\0");
		if (ulValue & kNkMAIDDataObjType_Image)
		{
			strcat(psString, "Image, ");
		}
		if (ulValue & kNkMAIDDataObjType_Sound)
		{
			strcat(psString, "Sound, ");
		}
		if (ulValue & kNkMAIDDataObjType_Video)
		{
			strcat(psString, "Video, ");
		}
		if (ulValue & kNkMAIDDataObjType_Thumbnail)
		{
			strcat(psString, "Thumbnail, ");
		}
		if (ulValue & kNkMAIDDataObjType_File)
		{
			strcat(psString, "File ");
		}
		strcat(psString, "\n");
		break;
	case kNkMAIDCapability_ModuleType:
		sprintf(buff, "%d : Scanner\n", kNkMAIDModuleType_Scanner);
		strcpy(psString, buff);
		sprintf(buff, "%d : Camera\n", kNkMAIDModuleType_Camera);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_WBFluorescentType:
		sprintf(buff, "%d : Sodium-vapor lamps\n", kNkWBFluorescentType_SodiumVapor);
		strcpy(psString, buff);
		sprintf(buff, "%d : Warm-white fluorescent\n", kNkWBFluorescentType_WarmWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : White fluorescent\n", kNkWBFluorescentType_White);
		strcat(psString, buff);
		sprintf(buff, "%d : Cool-white fluorescent\n", kNkWBFluorescentType_CoolWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : Day white fluorescent\n", kNkWBFluorescentType_DayWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : Daylight fluorescent\n", kNkWBFluorescentType_Daylight);
		strcat(psString, buff);
		sprintf(buff, "%d : High temp. mercury-vapor\n", kNkWBFluorescentType_HiTempMercuryVapor);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_LiveViewProhibit:
		strcpy(psString, "\0");
		if (ulValue == 0)
			strcat(psString, "No LiveViewProhibit ");
		if (ulValue & kNkMAIDLiveViewProhibit_Retractable)
		{
			strcat(psString, "Retractable Lens Warning, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_DuringMirrorup)
		{
			strcat(psString, "Mirrorup, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_BulbWarning)
		{
			strcat(psString, "Shutterspeed is time, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_TempRise)
		{
			strcat(psString, "High Temperature, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_Capture)
		{
			strcat(psString, "Executing Capture, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_NoCardLock)
		{
			strcat(psString, "No Card, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_SdramImg)
		{
			strcat(psString, "SDRAM image in camera, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_TTL)
		{
			strcat(psString, "TTL, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_Battery)
		{
			strcat(psString, "Battery, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_FEE)
		{
			strcat(psString, "FEE, ");
		}
		if (ulValue & kNkMAIDLiveViewProhibit_Sequence)
		{
			strcat(psString, "Sequence, ");
		}
		strcat(psString, "\n");
		break;
	case kNkMAIDCapability_LiveViewStatus:
		sprintf(buff, "%d : OFF\n", kNkMAIDLiveViewStatus_OFF);
		strcpy(psString, buff);
		sprintf(buff, "%d : ON\n", kNkMAIDLiveViewStatus_ON);
		strcat(psString, buff);
		sprintf(buff, "%d : ON_Menu\n", kNkMAIDLiveViewStatus_ON_Menu);
		strcat(psString, buff);
		sprintf(buff, "%d : ON_RemoteLV\n", kNkMAIDLiveViewStatus_ON_RemoteLV);
		strcat(psString, buff);
		sprintf(buff, "%d : ON_CameraLV\n", kNkMAIDLiveViewStatus_ON_CameraLV);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovRecInCardStatus:
		sprintf(buff, "%d : OFF\n", kNkMAIDMovRecInCardStatus_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : ON\n", kNkMAIDMovRecInCardStatus_On);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovRecInCardProhibit:
		strcpy(psString, "\0");
		if (ulValue == 0)
			strcat(psString, " Status is not movie recording prohibition, ");
		if (ulValue & kNkMAIDMovRecInCardProhibit_LVPhoto)
		{
			strcat(psString, "LiveViewPhoto, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_LVImageZoom)
		{
			strcat(psString, "LiveViewZoom, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_RecMov)
		{
			strcat(psString, "Recording movie, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_MovInBuf)
		{
			strcat(psString, "Movie in buffer, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_CardFull)
		{
			strcat(psString, "Card full, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_NoFormat)
		{
			strcat(psString, "Card unformatted, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_CardErr)
		{
			strcat(psString, "Card error, ");
		}
		if (ulValue & kNkMAIDMovRecInCardProhibit_NoCard)
		{
			strcat(psString, "No card, ");
		}
		strcat(psString, "\n");
		break;
	case kNkMAIDCapability_SaveMedia:
		sprintf(buff, "%d : Card\n", kNkMAIDSaveMedia_Card);
		strcpy(psString, buff);
		sprintf(buff, "%d : SDRAM\n", kNkMAIDSaveMedia_SDRAM);
		strcat(psString, buff);
		sprintf(buff, "%d : Card + SDRAM\n", kNkMAIDSaveMedia_Card_SDRAM);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_AFMode:
		sprintf(buff, "%d : AF-S\n", kNkMAIDAFMode_S);
		strcpy(psString, buff);
		sprintf(buff, "%d : AF-C\n", kNkMAIDAFMode_C);
		strcat(psString, buff);
		sprintf(buff, "%d : MF(fixed)\n", kNkMAIDAFMode_M_FIX);
		strcat(psString, buff);
		sprintf(buff, "%d : MF(selected)\n", kNkMAIDAFMode_M_SEL);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MirrorUpStatus:
		sprintf(buff, "%d : Mirror down\n", kNkMAIDMirrorUpStatus_Down);
		strcpy(psString, buff);
		sprintf(buff, "%d : Mirror up\n", kNkMAIDMirrorUpStatus_Up);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieMeteringMode:
		sprintf(buff, "%d : Matrix\n", kNkMAIDMovieMeteringMode_Matrix);
		strcpy(psString, buff);
		sprintf(buff, "%d : CenterWeighted\n", kNkMAIDMovieMeteringMode_CenterWeighted);
		strcat(psString, buff);
		sprintf(buff, "%d : HighLight\n", kNkMAIDMovieMeteringMode_HighLight);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_IPTCPresetSelect:
		sprintf(buff, "%d : OFF\n", kNkMAIDIPTCPresetSelect_OFF);
		strcpy(psString, buff);
		sprintf(buff, "%d - %d : PresetSelect1 - 10\n", kNkMAIDIPTCPresetSelect_1, kNkMAIDIPTCPresetSelect_10);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_AFLockOnAcross:
		sprintf(buff, "1(Quick) - 5(Slow)\n");
		strcpy(psString, buff);
		break;
	case kNkMAIDCapability_AFLockOnMove:
		sprintf(buff, "1(Steady) - 3(Erratic)\n");
		strcpy(psString, buff);
		break;
	case kNkMAIDCapability_FaceDetection:
		sprintf(buff, "%d : Off\n", kNkMAIDFaceDetection_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : On\n", kNkMAIDFaceDetection_On);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MatrixMetering:
		sprintf(buff, "%d : Off\n", kNkMAIDMatrixMetering_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : On\n", kNkMAIDMatrixMetering_On);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ExposureCompFlashUsed:
		sprintf(buff, "%d : Entireframe\n", kNkMAIDExposureCompFlashUsed_Entireframe);
		strcpy(psString, buff);
		sprintf(buff, "%d : Backgroundonly\n", kNkMAIDExposureCompFlashUsed_Backgroundonly);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ElectronicFrontCurtainShutter:
		sprintf(buff, "%d : Off\n", kNkMAIDElectronicFrontCurtainShutter_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : On\n", kNkMAIDElectronicFrontCurtainShutter_On);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_GetIPTCInfo:
		sprintf(buff, "%d : IPTC enbedded\n", kNkMAIDGetIPTCInfo_None);
		strcpy(psString, buff);
		sprintf(buff, "%d : IPTC not enbedded\n", kNkMAIDGetIPTCInfo_Attached);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_AllTestFiringDisable:
		sprintf(buff, "%d : Flash permitt\n", kNkMAIDAllTestFiringDisable_Enable);
		strcpy(psString, buff);
		sprintf(buff, "%d : Flash off\n", kNkMAIDAllTestFiringDisable_Disable);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_RadioMultipleFlashChannel:
		sprintf(buff, "%d : Unknown\n", kNkMAIDRadioMultipleFlashChannel_Unknown);
		strcpy(psString, buff);
		sprintf(buff, "%d : 5CH\n", kNkMAIDRadioMultipleFlashChannel_5ch);
		strcat(psString, buff);
		sprintf(buff, "%d : 10CH\n", kNkMAIDRadioMultipleFlashChannel_10ch);
		strcat(psString, buff);
		sprintf(buff, "%d : 15CH\n", kNkMAIDRadioMultipleFlashChannel_15ch);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_FlickerReductionSetting:
		sprintf(buff, "%d : Off\n", kNkMAIDFlickerReductionSetting_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : On\n", kNkMAIDFlickerReductionSetting_On);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieActive_D_Lighting:
		sprintf(buff, "%d : Off\n", kNkMAIDMovieActive_D_Lighting_Off);
		strcpy(psString, buff);
		sprintf(buff, "%d : Low\n", kNkMAIDMovieActive_D_Lighting_Low);
		strcat(psString, buff);
		sprintf(buff, "%d : Normal\n", kNkMAIDMovieActive_D_Lighting_Normal);
		strcat(psString, buff);
		sprintf(buff, "%d : High\n", kNkMAIDMovieActive_D_Lighting_High);
		strcat(psString, buff);
		sprintf(buff, "%d : Extra high\n", kNkMAIDMovieActive_D_Lighting_ExtraHigh);
		strcat(psString, buff);
		sprintf(buff, "%d : Same as photo\n", kNkMAIDMovieActive_D_Lighting_SamePhoto);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ElectronicVR:
		sprintf(buff, "%d : Off\n", kMAIDElectronicVR_OFF);
		strcat(psString, buff);
		sprintf(buff, "%d : On\n", kMAIDElectronicVR_ON);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_LiveViewZoomArea:
	{
		sprintf(buff, "%d :ZoomArea_0\n", kNkMAIDLiveViewZoomArea_0);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_360\n", kNkMAIDLiveViewZoomArea_360);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_512\n", kNkMAIDLiveViewZoomArea_512);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_640\n", kNkMAIDLiveViewZoomArea_640);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_720\n", kNkMAIDLiveViewZoomArea_720);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_1024\n", kNkMAIDLiveViewZoomArea_1024);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_1280\n", kNkMAIDLiveViewZoomArea_1280);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_1448\n", kNkMAIDLiveViewZoomArea_1448);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_2048\n", kNkMAIDLiveViewZoomArea_2048);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_2560\n", kNkMAIDLiveViewZoomArea_2560);
		strcat(psString, buff);
		sprintf(buff, "%d :ZoomArea_2896\n", kNkMAIDLiveViewZoomArea_2896);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_LiveViewSelector:
		sprintf(buff, "%d : Photo\n", kNkMAIDLiveViewSelector_Photo);
		strcat(psString, buff);
		sprintf(buff, "%d :Movie\n", kNkMAIDLiveViewSelector_Movie);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_LiveViewPhotoShootingMode:
		sprintf(buff, "%d : PhotoShootingMode2_OFF\n", kNkMAIDLiveViewPhotoShootingMode2_OFF);
		strcat(psString, buff);
		sprintf(buff, "%d :PhotoShootingMode2_Mode1\n", kNkMAIDLiveViewPhotoShootingMode2_Mode1);
		strcat(psString, buff);
		sprintf(buff, "%d :PhotoShootingMode2_Mode2\n", kNkMAIDLiveViewPhotoShootingMode2_Mode2);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_LiveViewImageStatus:
		sprintf(buff, "%d : ImageStatus_CannotAcquire\n", kNkMAIDLiveViewImageStatus_CannotAcquire);
		strcat(psString, buff);
		sprintf(buff, "%d :ImageStatus_CanAcquire\n", kNkMAIDLiveViewImageStatus_CanAcquire);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieRecMicrophone:
		sprintf(buff, "%d : MovRecMicrophone_Auto \n", kNkMAIDMovRecMicrophone_Auto);
		strcat(psString, buff);
		sprintf(buff, "%d :MovRecMicrophone_High  \n", kNkMAIDMovRecMicrophone_High);
		strcat(psString, buff);
		sprintf(buff, "%d : MovRecMicrophone_Medium \n", kNkMAIDMovRecMicrophone_Medium);
		strcat(psString, buff);
		sprintf(buff, "%d :MovRecMicrophone_Low  \n", kNkMAIDMovRecMicrophone_Low);
		strcat(psString, buff);
		sprintf(buff, "%d :MovRecMicrophone_Off  \n", kNkMAIDMovRecMicrophone_Off);
		strcat(psString, buff);
		sprintf(buff, "%d :MovRecMicrophone_Manual  \n", kNkMAIDMovRecMicrophone_Manual);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieRecordingZone:
	{
		sprintf(buff, "%d :RecordingZone_WideRange  \n", kNkMAIDMovieRecordingZone_WideRange);
		strcat(psString, buff);
		sprintf(buff, "%d :RecordingZone_VocalRange  \n", kNkMAIDMovieRecordingZone_VocalRange);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_MovieFileType:
	{
		sprintf(buff, "%d :FileType_MOV  \n", kNkMAIDMovieFileType_MOV);
		strcat(psString, buff);
		sprintf(buff, "%d :FileType_MP4  \n", kNkMAIDMovieFileType_MP4);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_MovieImageQuality:
	{
		sprintf(buff, "%d :FileType_MOV  \n", kNkMAIDMovieFileType_MOV);
		strcat(psString, buff);
		sprintf(buff, "%d :FileType_MP4  \n", kNkMAIDMovieFileType_MP4);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_RecordTimeCodes:
		sprintf(buff, "%d : RecordTimeCodes_Off\n", kNkMAIDRecordTimeCodes_Off);
		strcat(psString, buff);
		sprintf(buff, "%d : RecordTimeCodes_On\n", kNkMAIDRecordTimeCodes_On);
		strcat(psString, buff);
		sprintf(buff, "%d : RecordTimeCodes_OnWithHDMIOutput\n", kNkMAIDRecordTimeCodes_OnWithHDMIOutput);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_SpotWBMode:
		sprintf(buff, "%d : SpotWBMode_OFF\n", kNkMAIDSpotWBMode_OFF);
		strcat(psString, buff);
		sprintf(buff, "%d : SpotWBMode_ON\n", kNkMAIDSpotWBMode_ON);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_WBAutoType:
		sprintf(buff, "%d : AutoType_Normal\n", kNkWBAutoType_Normal);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_WarmWhite\n", kNkWBAutoType_WarmWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepWhite\n", kNkWBAutoType_KeepWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepAtmosphere\n", kNkWBAutoType_KeepAtmosphere);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieWBMode:
	{
	}
	break;
	case kNkMAIDCapability_MovieWBFluorescentType:
		sprintf(buff, "%d : SodiumVapor\n", kNkMovieWBFluorescentType_SodiumVapor);
		strcat(psString, buff);
		sprintf(buff, "%d : WarmWhite\n", kNkMovieWBFluorescentType_WarmWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : White\n", kNkMovieWBFluorescentType_White);
		strcat(psString, buff);
		sprintf(buff, "%d : CoolWhite\n", kNkMovieWBFluorescentType_CoolWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : DayWhite\n", kNkMovieWBFluorescentType_DayWhite);
		strcat(psString, buff);
		sprintf(buff, "%d : Daylight\n", kNkMovieWBFluorescentType_Daylight);
		strcat(psString, buff);
		sprintf(buff, "%d : HiTempMercuryVapor\n", kNkMovieWBFluorescentType_HiTempMercuryVapor);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieSensitivity:
	{
	}
	break;
	case kNkMAIDCapability_LensType:
	{
		//eNkMAIDLensType
		if (ulValue & kNkMAIDLensType_D)
			printf("%s", "LensType_D\n");
		if (ulValue & kNkMAIDLensType_G)
			printf("%s", "LensType_G\n");
		if (ulValue & kNkMAIDLensType_VR)
			printf("%s", "LensType_VR\n");
		if (ulValue & kNkMAIDLensType_DX)
			printf("%s", "LensType_DX\n");
		if (ulValue & kNkMAIDLensType_AFS)
			printf("%s", "LensType_AFS\n");
		if (ulValue & kNkMAIDLensType_AD)
			printf("%s", "LensType_AD\n");
		if (ulValue & kNkMAIDLensType_RET)
			printf("%s", "LensType_RET\n");
		if (ulValue & kNkMAIDLensType_E)
			printf("%s", "LensType_E\n");
		if (ulValue & kNkMAIDLensType_STM)
			printf("%s", "LensType_STM\n");
		if (ulValue & kNkMAIDLensType_CD)
			printf("%s", "LensType_CD\n");
	}
	break;
	case kNkMAIDCapability_MFDrive:
		sprintf(buff, "%d : InfinityToClosest\n", kNkMAIDMFDrive_InfinityToClosest);
		strcat(psString, buff);
		sprintf(buff, "%d : ClosestToInfinity\n", kNkMAIDMFDrive_ClosestToInfinity);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ShootingMode:
		sprintf(buff, "%d : AutoType_Normal\n", eNkMAIDShootingMode_S);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_WarmWhite\n", eNkMAIDShootingMode_C);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepWhite\n", eNkMAIDShootingMode_CH);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepAtmosphere\n", eNkMAIDShootingMode_SelfTimer);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_Normal\n", eNkMAIDShootingMode_MirrorUp);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_WarmWhite\n", eNkMAIDShootingMode_RemoteTimer_Instant);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepWhite\n", eNkMAIDShootingMode_RemoteTimer_2sec);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepAtmosphere\n", eNkMAIDShootingMode_RemoteCtrl);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_KeepAtmosphere\n", eNkMAIDShootingMode_QuietC);
		strcat(psString, buff);
		sprintf(buff, "%d : AutoType_Normal\n", eNkMAIDShootingMode_CHPriorityFrame);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ContrastAF:
		sprintf(buff, "%u : ContrastAF_Start (Set Only)\n", kNkMAIDContrastAF_Start);
		strcat(psString, buff);
		sprintf(buff, "%u : ContrastAF_Stop (Set Only)\n", kNkMAIDContrastAF_Stop);
		strcat(psString, buff);
		sprintf(buff, "%u : ContrastAF_OK (Get Only)\n", kNkMAIDContrastAF_OK);
		strcat(psString, buff);
		sprintf(buff, "%u : ContrastAF_OutOfFocus (Get Only)\n", kNkMAIDContrastAF_OutOfFocus);
		strcat(psString, buff);
		sprintf(buff, "%u : ContrastAF_Busy (Get Only)\n", kNkMAIDContrastAF_Busy);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ExternalFlashSort:
		sprintf(buff, "%u : ExternalFlashSort_NoCommunicate\n", eNkMAIDExternalFlashSort_NoCommunicate);
		strcat(psString, buff);
		sprintf(buff, "%u : ExternalFlashSort_OldType\n", eNkMAIDExternalFlashSort_OldType);
		strcat(psString, buff);
		sprintf(buff, "%u : ExternalFlashSort_NewType\n", eNkMAIDExternalFlashSort_NewType);
		strcat(psString, buff);
		sprintf(buff, "%u : ExternalFlashSort_NotExist\n", eNkMAIDExternalFlashSort_NotExist);
		strcat(psString, buff);
		sprintf(buff, "%u : ExternalFlashSort_NewTypeControl\n", eNkMAIDExternalFlashSort_NewTypeControl);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_ExternalFlashStatus:
		sprintf(buff, "%u : ExternalFlashStatus_Ready\n", kNkMAIDExternalFlashStatus_Ready);
		strcat(psString, buff);
		sprintf(buff, "%u : ExternalFlashStatus_NotReady\n", kNkMAIDExternalFlashStatus_NotReady);
		strcat(psString, buff);
		sprintf(buff, "%u : ExternalFlashStatus_NotExist\n", kNkMAIDExternalFlashStatus_NotExist);
		strcat(psString, buff);
		break;
	case kNkMAIDCapability_MovieWBAutoType:
	{
		sprintf(buff, "%u : WBAutoType_Normal\n", kNkMovieWBAutoType_Normal);
		strcat(psString, buff);
		sprintf(buff, "%u : AutoType_WarmWhite\n", kNkMovieWBAutoType_WarmWhite);
		strcat(psString, buff);
		sprintf(buff, "%u : AutoType_KeepWhite\n", kNkMovieWBAutoType_KeepWhite);
		strcat(psString, buff);
		sprintf(buff, "%u :AutoType_KeepAtmosphere\n", kNkMovieWBAutoType_KeepAtmosphere);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_MovieScreenSize:
	{
		sprintf(buff, "%u : QFHD_30p\n", kNkMAIDMovieScreenSize8_QFHD_30p);
		strcat(psString, buff);
		sprintf(buff, "%u : QFHD_25p\n", kNkMAIDMovieScreenSize8_QFHD_25p);
		strcat(psString, buff);
		sprintf(buff, "%u : QFHD_24p\n", kNkMAIDMovieScreenSize8_QFHD_24p);
		strcat(psString, buff);
		sprintf(buff, "%u :FullHD_60p\n", kNkMAIDMovieScreenSize8_FullHD_60p);
		strcat(psString, buff);
		sprintf(buff, "%u : FullHD_50p\n", kNkMAIDMovieScreenSize8_FullHD_50p);
		strcat(psString, buff);
		sprintf(buff, "%u : FullHD_30p\n", kNkMAIDMovieScreenSize8_FullHD_30p);
		strcat(psString, buff);
		sprintf(buff, "%u : FullHD_25p\n", kNkMAIDMovieScreenSize8_FullHD_25p);
		strcat(psString, buff);
		sprintf(buff, "%u :FullHD_24p\n", kNkMAIDMovieScreenSize8_FullHD_24p);
		strcat(psString, buff);
		sprintf(buff, "%u : 820p_60p\n", kNkMAIDMovieScreenSize8_820p_60p);
		strcat(psString, buff);
		sprintf(buff, "%u : 820p_50p\n", kNkMAIDMovieScreenSize8_820p_50p);
		strcat(psString, buff);
		sprintf(buff, "%u : 60p_Crop\n", kNkMAIDMovieScreenSize8_FullHD_60p_Crop);
		strcat(psString, buff);
		sprintf(buff, "%u :50p_Crop\n", kNkMAIDMovieScreenSize8_FullHD_50p_Crop);
		strcat(psString, buff);
		sprintf(buff, "%u : 30p_Crop\n", kNkMAIDMovieScreenSize8_FullHD_30p_Crop);
		strcat(psString, buff);
		sprintf(buff, "%u : 25p_Crop\n", kNkMAIDMovieScreenSize8_FullHD_25p_Crop);
		strcat(psString, buff);
		sprintf(buff, "%u : 24p_Crop\n", kNkMAIDMovieScreenSize8_FullHD_24p_Crop);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_ISOAutoShutterTime:
	{
		sprintf(buff, "%d : 1/125 - Sec\n", kNkMAIDISOAutoShutterTime_0);
		strcat(psString, buff);
		sprintf(buff, "%d : 1/60 - Sec\n", kNkMAIDISOAutoShutterTime_1);
		strcat(psString, buff);
		sprintf(buff, "%d : 1/30 - Sec\n", kNkMAIDISOAutoShutterTime_2);
		strcat(psString, buff);
		sprintf(buff, "%d : 1/15 - Sec\n", kNkMAIDISOAutoShutterTime_3);
		strcat(psString, buff);
		sprintf(buff, "%d : 1/8 - Sec\n", kNkMAIDISOAutoShutterTime_4);
		strcat(psString, buff);
		sprintf(buff, "%d : 1/4 - Sec\n", kNkMAIDISOAutoShutterTime_5);
		strcat(psString, buff);
		sprintf(buff, "%d :  1/2 - Sec\n", kNkMAIDISOAutoShutterTime_6);
		strcat(psString, buff);
		sprintf(buff, "%d : 1 - Sec\n", kNkMAIDISOAutoShutterTime_7);
		strcat(psString, buff);
		sprintf(buff, "%d : 2 - Sec\n", kNkMAIDISOAutoShutterTime_8);
		strcat(psString, buff);
		sprintf(buff, "%d : 4 - Sec\n", kNkMAIDISOAutoShutterTime_9);
		strcat(psString, buff);
		sprintf(buff, "%u : 8 - Sec\n", kNkMAIDISOAutoShutterTime_10);
		strcat(psString, buff);
		sprintf(buff, "%u : 15 - Sec\n", kNkMAIDISOAutoShutterTime_11);
		strcat(psString, buff);
		sprintf(buff, "%u : 30 - Sec\n", kNkMAIDISOAutoShutterTime_12);
		strcat(psString, buff);
		sprintf(buff, "%u :1/250 - Sec\n", kNkMAIDISOAutoShutterTime_13);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/200 - Sec\n", kNkMAIDISOAutoShutterTime_14);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/160 - Sec\n", kNkMAIDISOAutoShutterTime_15);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/100 - Sec\n", kNkMAIDISOAutoShutterTime_16);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/80 - Sec\n", kNkMAIDISOAutoShutterTime_17);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/40 - Sec\n", kNkMAIDISOAutoShutterTime_18);
		strcat(psString, buff);
		sprintf(buff, "%u :1/50 - Sec\n", kNkMAIDISOAutoShutterTime_19);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/4000 - Sec\n", kNkMAIDISOAutoShutterTime_20);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/3200 - Sec\n", kNkMAIDISOAutoShutterTime_21);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/2500 - Sec\n", kNkMAIDISOAutoShutterTime_22);
		strcat(psString, buff);
		sprintf(buff, "%u :1/2000 - Sec\n", kNkMAIDISOAutoShutterTime_23);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/1600 - Sec\n", kNkMAIDISOAutoShutterTime_24);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/1250 - Sec\n", kNkMAIDISOAutoShutterTime_25);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/1000 - Sec\n", kNkMAIDISOAutoShutterTime_26);
		strcat(psString, buff);
		sprintf(buff, "%u :1/800 - Sec\n", kNkMAIDISOAutoShutterTime_27);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/640 - Sec\n", kNkMAIDISOAutoShutterTime_28);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/500 - Sec\n", kNkMAIDISOAutoShutterTime_29);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/400 - Sec\n", kNkMAIDISOAutoShutterTime_30);
		strcat(psString, buff);
		sprintf(buff, "%u :1/320 - Sec\n", kNkMAIDISOAutoShutterTime_31);
		strcat(psString, buff);
		sprintf(buff, "%u : Auto - Sec\n", kNkMAIDISOAutoShutterTime_32);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/25 - Sec\n", kNkMAIDISOAutoShutterTime_33);
		strcat(psString, buff);
		sprintf(buff, "%u :1/20 - Sec\n", kNkMAIDISOAutoShutterTime_34);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/13 - Sec\n", kNkMAIDISOAutoShutterTime_35);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/10 - Sec\n", kNkMAIDISOAutoShutterTime_36);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/6 - Sec\n", kNkMAIDISOAutoShutterTime_37);
		strcat(psString, buff);
		sprintf(buff, "%u :1/5 - Sec\n", kNkMAIDISOAutoShutterTime_38);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/3 - Sec \n", kNkMAIDISOAutoShutterTime_39);
		strcat(psString, buff);
		sprintf(buff, "%u :1/2.5 - Sec\n", kNkMAIDISOAutoShutterTime_40);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/1.6 - Sec\n", kNkMAIDISOAutoShutterTime_41);
		strcat(psString, buff);
		sprintf(buff, "%u : 1/1.3 - Sec\n", kNkMAIDISOAutoShutterTime_42);
		strcat(psString, buff);
		sprintf(buff, "%u :1.3 - Sec\n", kNkMAIDISOAutoShutterTime_43);
		strcat(psString, buff);
		sprintf(buff, "%u : 1.6 - Sec\n", kNkMAIDISOAutoShutterTime_44);
		strcat(psString, buff);
		sprintf(buff, "%u : 2.5 - Sec\n", kNkMAIDISOAutoShutterTime_45);
		strcat(psString, buff);
		sprintf(buff, "%u :3 - Sec\n", kNkMAIDISOAutoShutterTime_46);
		strcat(psString, buff);
		sprintf(buff, "%u : 5 - Sec\n", kNkMAIDISOAutoShutterTime_47);
		strcat(psString, buff);
		sprintf(buff, "%u : 6 - Sec\n", kNkMAIDISOAutoShutterTime_48);
		strcat(psString, buff);
		sprintf(buff, "%u : 10 - Sec\n", kNkMAIDISOAutoShutterTime_49);
		strcat(psString, buff);
		sprintf(buff, "%u :13 - Sec\n", kNkMAIDISOAutoShutterTime_50);
		strcat(psString, buff);
		sprintf(buff, "%u : 20 - Sec\n", kNkMAIDISOAutoShutterTime_51);
		strcat(psString, buff);
		sprintf(buff, "%u :25 - Sec\n", kNkMAIDISOAutoShutterTime_52);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_ISOAutoHiLimit:
	{
		sprintf(buff, "%u : ISO200\n", kNkMAIDISOAutoHiLimitCommon_ISO200);
		strcpy(psString, buff);
		sprintf(buff, "%u : ISO250\n", kNkMAIDISOAutoHiLimitCommon_ISO250);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO280\n", kNkMAIDISOAutoHiLimitCommon_ISO280);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO320\n", kNkMAIDISOAutoHiLimitCommon_ISO320);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO400\n", kNkMAIDISOAutoHiLimitCommon_ISO400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO500\n", kNkMAIDISOAutoHiLimitCommon_ISO500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO560\n", kNkMAIDISOAutoHiLimitCommon_ISO560);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO640\n", kNkMAIDISOAutoHiLimitCommon_ISO640);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO800\n", kNkMAIDISOAutoHiLimitCommon_ISO800);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1000\n", kNkMAIDISOAutoHiLimitCommon_ISO1000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1100\n", kNkMAIDISOAutoHiLimitCommon_ISO1100);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1250\n", kNkMAIDISOAutoHiLimitCommon_ISO1250);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1600\n", kNkMAIDISOAutoHiLimitCommon_ISO1600);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2000\n", kNkMAIDISOAutoHiLimitCommon_ISO2000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2200\n", kNkMAIDISOAutoHiLimitCommon_ISO2200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2500\n", kNkMAIDISOAutoHiLimitCommon_ISO2500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO3200\n", kNkMAIDISOAutoHiLimitCommon_ISO3200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO4000\n", kNkMAIDISOAutoHiLimitCommon_ISO4000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO4500\n", kNkMAIDISOAutoHiLimitCommon_ISO4500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO5000\n", kNkMAIDISOAutoHiLimitCommon_ISO5000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO6400\n", kNkMAIDISOAutoHiLimitCommon_ISO6400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO8000\n", kNkMAIDISOAutoHiLimitCommon_ISO8000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO9000\n", kNkMAIDISOAutoHiLimitCommon_ISO9000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO10000\n", kNkMAIDISOAutoHiLimitCommon_ISO10000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO12800\n", kNkMAIDISOAutoHiLimitCommon_ISO12800);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO16000\n", kNkMAIDISOAutoHiLimitCommon_ISO16000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO18000\n", kNkMAIDISOAutoHiLimitCommon_ISO18000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO20000\n", kNkMAIDISOAutoHiLimitCommon_ISO20000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO25600\n", kNkMAIDISOAutoHiLimitCommon_ISO25600);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO32000\n", kNkMAIDISOAutoHiLimitCommon_ISO32000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO36000\n", kNkMAIDISOAutoHiLimitCommon_ISO36000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO40000\n", kNkMAIDISOAutoHiLimitCommon_ISO40000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO51200\n", kNkMAIDISOAutoHiLimitCommon_ISO51200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO64000\n", kNkMAIDISOAutoHiLimitCommon_ISO64000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO72000\n", kNkMAIDISOAutoHiLimitCommon_ISO72000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO81200\n", kNkMAIDISOAutoHiLimitCommon_ISO81200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO102400\n", kNkMAIDISOAutoHiLimitCommon_ISO102400);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi03\n", kNkMAIDISOAutoHiLimitCommon_ISOHi03);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi05\n", kNkMAIDISOAutoHiLimitCommon_ISOHi05);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi07\n", kNkMAIDISOAutoHiLimitCommon_ISOHi07);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi1\n", kNkMAIDISOAutoHiLimitCommon_ISOHi10);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi2\n", kNkMAIDISOAutoHiLimitCommon_ISOHi20);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi3\n", kNkMAIDISOAutoHiLimitCommon_ISOHi30);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi4\n", kNkMAIDISOAutoHiLimitCommon_ISOHi40);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi5\n", kNkMAIDISOAutoHiLimitCommon_ISOHi50);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO72\n", kNkMAIDISOAutoHiLimitCommon_ISO72);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO80\n", kNkMAIDISOAutoHiLimitCommon_ISO80);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO100\n", kNkMAIDISOAutoHiLimitCommon_ISO100);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO125\n", kNkMAIDISOAutoHiLimitCommon_ISO125);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO140\n", kNkMAIDISOAutoHiLimitCommon_ISO140);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO160\n", kNkMAIDISOAutoHiLimitCommon_ISO160);
		strcat(psString, buff);

	}
	break;
	case kNkMAIDCapability_FlashISOAutoHighLimit:
	{
		sprintf(buff, "%u : ISO200\n", kNkMAIDFlashISOAutoHighLimit_ISO200);
		strcpy(psString, buff);
		sprintf(buff, "%u : ISO250\n", kNkMAIDFlashISOAutoHighLimit_ISO250);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO280\n", kNkMAIDFlashISOAutoHighLimit_ISO280);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO320\n", kNkMAIDFlashISOAutoHighLimit_ISO320);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO400\n", kNkMAIDFlashISOAutoHighLimit_ISO400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO500\n", kNkMAIDFlashISOAutoHighLimit_ISO500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO560\n", kNkMAIDFlashISOAutoHighLimit_ISO560);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO640\n", kNkMAIDFlashISOAutoHighLimit_ISO640);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO800\n", kNkMAIDFlashISOAutoHighLimit_ISO800);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1000\n", kNkMAIDFlashISOAutoHighLimit_ISO1000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1100\n", kNkMAIDFlashISOAutoHighLimit_ISO1100);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1250\n", kNkMAIDFlashISOAutoHighLimit_ISO1250);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1600\n", kNkMAIDFlashISOAutoHighLimit_ISO1600);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2000\n", kNkMAIDFlashISOAutoHighLimit_ISO2000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2200\n", kNkMAIDFlashISOAutoHighLimit_ISO2200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2500\n", kNkMAIDFlashISOAutoHighLimit_ISO2500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO3200\n", kNkMAIDFlashISOAutoHighLimit_ISO3200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO4000\n", kNkMAIDFlashISOAutoHighLimit_ISO4000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO4500\n", kNkMAIDFlashISOAutoHighLimit_ISO4500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO5000\n", kNkMAIDFlashISOAutoHighLimit_ISO5000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO6400\n", kNkMAIDFlashISOAutoHighLimit_ISO6400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO8000\n", kNkMAIDFlashISOAutoHighLimit_ISO8000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO9000\n", kNkMAIDFlashISOAutoHighLimit_ISO9000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO10000\n", kNkMAIDFlashISOAutoHighLimit_ISO10000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO12800\n", kNkMAIDFlashISOAutoHighLimit_ISO12800);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO16000\n", kNkMAIDFlashISOAutoHighLimit_ISO16000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO18000\n", kNkMAIDFlashISOAutoHighLimit_ISO18000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO20000\n", kNkMAIDFlashISOAutoHighLimit_ISO20000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO25600\n", kNkMAIDFlashISOAutoHighLimit_ISO25600);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO32000\n", kNkMAIDFlashISOAutoHighLimit_ISO32000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO36000\n", kNkMAIDFlashISOAutoHighLimit_ISO36000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO40000\n", kNkMAIDFlashISOAutoHighLimit_ISO40000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO51200\n", kNkMAIDFlashISOAutoHighLimit_ISO51200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO64000\n", kNkMAIDFlashISOAutoHighLimit_ISO64000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO72000\n", kNkMAIDFlashISOAutoHighLimit_ISO72000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO81200\n", kNkMAIDFlashISOAutoHighLimit_ISO81200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO102400\n", kNkMAIDFlashISOAutoHighLimit_ISO102400);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi03\n", kNkMAIDFlashISOAutoHighLimit_Hi03);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi05\n", kNkMAIDFlashISOAutoHighLimit_Hi05);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi07\n", kNkMAIDFlashISOAutoHighLimit_Hi07);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi1\n", kNkMAIDFlashISOAutoHighLimit_Hi1);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi2\n", kNkMAIDFlashISOAutoHighLimit_Hi2);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi3\n", kNkMAIDFlashISOAutoHighLimit_Hi3);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi4\n", kNkMAIDFlashISOAutoHighLimit_Hi4);
		strcat(psString, buff);
		sprintf(buff, "%u : Hi5\n", kNkMAIDFlashISOAutoHighLimit_Hi5);
		strcat(psString, buff);
		sprintf(buff, "%u : NoneFlash\n", kNkMAIDFlashISOAutoHighLimit_NoneFlash);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO72\n", kNkMAIDFlashISOAutoHighLimit_ISO72);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO80\n", kNkMAIDFlashISOAutoHighLimit_ISO80);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO100\n", kNkMAIDFlashISOAutoHighLimit_ISO100);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO125\n", kNkMAIDFlashISOAutoHighLimit_ISO125);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO140\n", kNkMAIDFlashISOAutoHighLimit_ISO140);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO160\n", kNkMAIDFlashISOAutoHighLimit_ISO160);
		strcat(psString, buff);
	}
	break;
	case kNkMAIDCapability_MovieISOAutoHiLimit:
	{
		sprintf(buff, "%u : ISO200\n", kNkMAIDMovieISOAutoHiLimit3_ISO200);
		strcpy(psString, buff);
		sprintf(buff, "%u : ISO250\n", kNkMAIDMovieISOAutoHiLimit3_ISO250);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO280\n", kNkMAIDMovieISOAutoHiLimit3_ISO280);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO320\n", kNkMAIDMovieISOAutoHiLimit3_ISO320);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO400\n", kNkMAIDMovieISOAutoHiLimit3_ISO400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO500\n", kNkMAIDMovieISOAutoHiLimit3_ISO500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO560\n", kNkMAIDMovieISOAutoHiLimit3_ISO560);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO640\n", kNkMAIDMovieISOAutoHiLimit3_ISO640);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO800\n", kNkMAIDMovieISOAutoHiLimit3_ISO800);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1000\n", kNkMAIDMovieISOAutoHiLimit3_ISO1000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1100\n", kNkMAIDMovieISOAutoHiLimit3_ISO1100);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1250\n", kNkMAIDMovieISOAutoHiLimit3_ISO1250);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO1600\n", kNkMAIDMovieISOAutoHiLimit3_ISO1600);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2000\n", kNkMAIDMovieISOAutoHiLimit3_ISO2000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2200\n", kNkMAIDMovieISOAutoHiLimit3_ISO2200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO2500\n", kNkMAIDMovieISOAutoHiLimit3_ISO2500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO3200\n", kNkMAIDMovieISOAutoHiLimit3_ISO3200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO4000\n", kNkMAIDMovieISOAutoHiLimit3_ISO4000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO4500\n", kNkMAIDMovieISOAutoHiLimit3_ISO4500);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO5000\n", kNkMAIDMovieISOAutoHiLimit3_ISO5000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO6400\n", kNkMAIDMovieISOAutoHiLimit3_ISO6400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO8000\n", kNkMAIDMovieISOAutoHiLimit3_ISO8000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO9000\n", kNkMAIDMovieISOAutoHiLimit3_ISO9000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO10000\n", kNkMAIDMovieISOAutoHiLimit3_ISO10000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO12800\n", kNkMAIDMovieISOAutoHiLimit3_ISO12800);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi03\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi03);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi05\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi05);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi07\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi07);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi10\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi10);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi20\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi20);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO16000\n", kNkMAIDMovieISOAutoHiLimit3_ISO16000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO18000\n", kNkMAIDMovieISOAutoHiLimit3_ISO18000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO20000\n", kNkMAIDMovieISOAutoHiLimit3_ISO20000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO25600\n", kNkMAIDMovieISOAutoHiLimit3_ISO25600);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO32000\n", kNkMAIDMovieISOAutoHiLimit3_ISO32000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO36000\n", kNkMAIDMovieISOAutoHiLimit3_ISO36000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO40000\n", kNkMAIDMovieISOAutoHiLimit3_ISO40000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO51200\n", kNkMAIDMovieISOAutoHiLimit3_ISO51200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO64000\n", kNkMAIDMovieISOAutoHiLimit3_ISO64000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO72000\n", kNkMAIDMovieISOAutoHiLimit3_ISO72000);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO81200\n", kNkMAIDMovieISOAutoHiLimit3_ISO81200);
		strcat(psString, buff);
		sprintf(buff, "%u : ISO102400\n", kNkMAIDMovieISOAutoHiLimit3_ISO102400);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi30\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi30);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi40\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi40);
		strcat(psString, buff);
		sprintf(buff, "%u : ISOHi50\n", kNkMAIDMovieISOAutoHiLimit3_ISOHi50);
		strcat(psString, buff);
	}
	break;
	default:
		psString[0] = '\0';
		break;
	}
	return psString;
}

BOOL SetBoolCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	int		new_val;
	char	buf[256];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_BooleanPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			if (*((bool*)pCapValue) == 0)
				printf("Cap Value = False\n");
			else
				printf("Cap Value = True\n");
		}

		freeByDataType(pCapValue, eDataType);
	}

	//check capability operation- whether we can set or not		

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	printf("Input new value\n>");
	printf("Input '1' to set True \n");
	printf("Input '2' to set False \n");
	scanf("%s", buf);
	new_val = atoi(buf);
	if ((new_val == 1) || (new_val == 2)) {

		unsigned char bFlag = (new_val == 1) ? true : false;
		lerror = g_pMAIDSetCapability(ulCapID, &bFlag, kNkMAIDDataType_BooleanPtr);
		PERROR(lerror);

	}
	else
	{
		printf("Invalid input\n");
		return false;
	}

	return true;

}

BOOL  SetStringCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	char	buf[256];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_StringPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			printf("Cap Value = %s\n", ((LPNkMAIDString)pCapValue)->str);
		}

		freeByDataType(pCapValue, eDataType);
	}

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	printf("Input new value\n>");

	scanf("%s", buf);
	lerror = g_pMAIDSetCapability(ulCapID, buf, kNkMAIDDataType_StringPtr);
	PERROR(lerror);
	return true;
}

BOOL SetAcceptDiskAcquisition()
{
	bool set_cap_applicable = false;
	NkMAIDString nString;
	memset(&nString, 0, sizeof(NkMAIDString));
	LPVOID pCapValue = &nString;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_AcceptDiskAcquisition, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_AcceptDiskAcquisition, ulDataType) == false)
		return FALSE;
	if (ulDataType != kNkMAIDCapType_Generic) return FALSE;

	NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_AcceptDiskAcquisition, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		printf("Failed to get capability value\n");
		return FALSE;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_GenericPtr)
		{
			printf("Invalid data type returned\n");
			return FALSE;
		}
		else
		{
			printf("Cap Value = %s\n", nString.str);
		}
	}

	if (CheckCapability(kNkMAIDCapability_AcceptDiskAcquisition, kNkMAIDCapOperation_Set) == false)
		return FALSE;

	char buf[1024];
	printf("\nEnter path\n");
	scanf("%s", buf);

	strcpy((char*)nString.str, buf);

	lerror = g_pMAIDSetCapability(kNkMAIDCapability_AcceptDiskAcquisition, &nString, kNkMAIDDataType_GenericPtr);
	PERROR(lerror);

	return TRUE;
}

BOOL SetPointCapability(ULONG ulCapID)
{
	NkMAIDPoint	stPoint;
	char	buf[256];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;
	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(ulCapID, ulDataType) == false)
		return false;
	if (ulDataType != kNkMAIDCapType_Point) return FALSE;

	printf("Input x\n>");
	scanf("%s", buf);
	stPoint.x = atoi(buf);
	printf("Input y\n>");
	scanf("%s", buf);
	stPoint.y = atoi(buf);

	NKERROR lerror = g_pMAIDSetCapability(ulCapID, &stPoint, kNkMAIDDataType_PointPtr);
	PERROR(lerror);

	return true;
}

BOOL SetIntegerCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	int new_val;
	char	buf[256];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_IntegerPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			printf("%s\n", GetUnsignedString(ulCapID, *((ULONG*)pCapValue), buf));
			printf("Current value = %d\n", *((LONG*)pCapValue));
		}

		freeByDataType(pCapValue, eDataType);
	}

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	printf("Input new value\n>");
	SetUnsignedString(ulCapID);
	scanf("%s", buf);
	new_val = atoi(buf);
	lerror = g_pMAIDSetCapability(ulCapID, &new_val, kNkMAIDDataType_Unsigned);
	PERROR(lerror);

	return true;
}

BOOL SetUnsignedIntCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	int new_val;
	char	buf[2048];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_UnsignedPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			printf("Cap Value = %u\n", *((ULONG*)pCapValue));
			memset(buf, 0, sizeof(buf));
			printf("%s\n", GetUnsignedString(ulCapID, *((ULONG*)pCapValue), buf));
		}

		freeByDataType(pCapValue, eDataType);
	}

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	printf("Input new value\n>");
	//SetUnsignedString(ulCapID);
	scanf("%s", buf);
	new_val = atoi(buf);
	lerror = g_pMAIDSetCapability(ulCapID, (LPVOID)&new_val, kNkMAIDDataType_UnsignedPtr);
	PERROR(lerror);

	return true;
}

BOOL GetIntegerCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	char	buf[256];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_IntegerPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			printf("Cap Value = %s\n", GetUnsignedString(ulCapID, *((ULONG*)pCapValue), buf));
			return true;
		}

		freeByDataType(pCapValue, eDataType);
		return true;
	}
}

BOOL GetUnsignedIntCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	char	buf[1024];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_UnsignedPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			printf("Cap Value = %u\n", *((ULONG*)pCapValue));
			memset(buf, 0, sizeof(buf));
			printf("%s\n", GetUnsignedString(ulCapID, *((ULONG*)pCapValue), buf));
			return true;
		}

		freeByDataType(pCapValue, eDataType);
		return true;
	}
}

BOOL SetEnumCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	int new_val;
	char buf[256];
	NKERROR lerror = kNkMAIDResult_NoError;

	bool set_cap_applicable = false;
	bool GetSettingSupportedValueArray = false;
#ifdef PERFORMANCECHECK
	//Performance check
	auto t1 = std::chrono::high_resolution_clock::now();
#endif
	GetSettingSupportedValueArray = CheckCapability(ulCapID, kNkMAIDCapOperation_GetArray);
	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NkMAIDEnum	stEnum = { 0 };
	//pCapValue = &stEnum;

	if (GetSettingSupportedValueArray)
	{
		lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingSupportedValueArray, pCapValue, eDataType);

		if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
		{
			if (pCapValue) freeByDataType(pCapValue, eDataType);
			printf("Failed to get capability value\n");
			return false;
		}
		else
		{
			if (eDataType != kNkMAIDDataType_EnumPtr)
			{
				printf("Invalid data type returned\n");
				freeByDataType(pCapValue, eDataType);
				return false;
			}
			else
			{
				stEnum = *((NkMAIDEnum*)pCapValue);
				if (printEnumCapArrayValues(ulCapID, stEnum) == false)
				{
					freeByDataType(pCapValue, eDataType);
					return FALSE;
				}
				freeByDataType(pCapValue, eDataType);
			}
		}
	}

	lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

#ifdef PERFORMANCECHECK
	//Performance
	auto t2 = std::chrono::high_resolution_clock::now();
	auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
	std::cout << "GetCapability Execution duration: " << duration << std::endl;
#endif
	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_EnumPtr)
		{
			printf("Invalid data type returned\n");
			freeByDataType(pCapValue, eDataType);
			return false;
		}
		else
		{
			stEnum = *((NkMAIDEnum*)pCapValue);
			printf("Cap Value = %d\n", stEnum.ulValue);
		}

		freeByDataType(pCapValue, eDataType);
	}

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	switch (stEnum.ulType)
	{
	case kNkMAIDArrayType_Unsigned:
	{
		printf("Input new value\n>");
		scanf("%s", buf);
		stEnum.ulValue = atoi(buf);
		stEnum.pData = NULL;
#ifdef PERFORMANCECHECK
		//Performance check
		auto t1 = std::chrono::high_resolution_clock::now();
#endif
		lerror = g_pMAIDSetCapability(ulCapID, &stEnum, kNkMAIDDataType_EnumPtr);

#ifdef PERFORMANCECHECK
		//Performance
		auto t2 = std::chrono::high_resolution_clock::now();
		auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
		std::cout << "SetCapability Execution duration: " << duration << std::endl;
#endif
	}
	break;
	case kNkMAIDArrayType_PackedString:
	{
		printf("Input new value\n>");
		scanf("%s", buf);
		stEnum.ulValue = atoi(buf);
		stEnum.pData = NULL;

#ifdef PERFORMANCECHECK	
		//Performance check
		auto t1 = std::chrono::high_resolution_clock::now();
#endif	
		lerror = g_pMAIDSetCapability(ulCapID, &stEnum, kNkMAIDDataType_EnumPtr);
#ifdef PERFORMANCECHECK	
		//Performance
		auto t2 = std::chrono::high_resolution_clock::now();
		auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
		std::cout << "SetCapability Execution duration: " << duration << std::endl;
#endif
	}
	break;
	case kNkMAIDArrayType_String:
	{
		printf("Input new value\n>");
		scanf("%s", buf);
		//new_val = atoi(buf);
#ifdef PERFORMANCECHECK
		//Performance check
		auto t1 = std::chrono::high_resolution_clock::now();
#endif	
		lerror = g_pMAIDSetCapability(ulCapID, buf, kNkMAIDDataType_StringPtr);
#ifdef PERFORMANCECHECK
		//Performance
		auto t2 = std::chrono::high_resolution_clock::now();
		auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
		std::cout << "SetCapability Execution duration: " << duration << std::endl;
#endif
	}
	break;

	case kNkMAIDArrayType_Boolean:
	{
		printf("Input new value\n>");
		printf("Input '1' to set True \n");
		printf("Input '2' to set False \n");
		scanf("%s", buf);
		new_val = atoi(buf);
		if ((new_val == 1) || (new_val == 2))
		{
			unsigned char bFlag = (new_val == 1) ? true : false;
#ifdef PERFORMANCECHECK
			//Performance check
			auto t1 = std::chrono::high_resolution_clock::now();
#endif
			lerror = g_pMAIDSetCapability(ulCapID, &bFlag, kNkMAIDDataType_BooleanPtr);
#ifdef PERFORMANCECHECK
			//Performance
			auto t2 = std::chrono::high_resolution_clock::now();
			auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1).count();
			std::cout << "SetCapability Execution duration: " << duration << std::endl;
#endif
		}
	}
	break;
	}

	free(stEnum.pData);

	return TRUE;
}

bool printEnumCapArrayValues(ULONG ulCapID, NkMAIDEnum stEnum)
{
	switch (ulCapID)
	{
	case kNkMAIDCapability_MoviePowerHiResZoomCollab:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case  MoviePowerHiResZoomCollab_OFF:
				printf("%u - OFF\n", i);
				break;
			case MoviePowerHiResZoomCollab_Extended:
				printf("%u - Extended\n", i);
				break;
			case MoviePowerHiResZoomCollab_Synchronized:
				printf("%u - Synchronized\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieShutterAngle:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case  kNkMAIDMovieShutterAngle_180_00:
				printf("%u - 180.00\n", i);
				break;
			case kNkMAIDMovieShutterAngle_360_00:
				printf("%u - 360\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieShutterMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case  kNkMAIDMovieShutterMode_ShutterSpeed:
				printf("%u - ShutterSpeed\n", i);
				break;
			case kNkMAIDMovieShutterMode_ShutterAngle:
				printf("%u - ShutterAngle\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case  kNkMAIDCapability_DropFrame:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case  kNkMAIDDropFrame_Off:
				printf("%u - kNkMAIDDropFrame_Off\n", i);
				break;
			case kNkMAIDDropFrame_On:
				printf("%u - kNkMAIDDropFrame_On\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case  kNkMAIDCapability_CountUpMethod:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case  kNkMAIDCountUpMethod_RecordRun:
				printf("%u - kNkMAIDCountUpMethod_RecordRun\n", i);
				break;
			case kNkMAIDCountUpMethod_FreeRun:
				printf("%u - kNkMAIDCountUpMethod_FreeRun\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case  kNkMAIDCapability_HiResZoom:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNKMAIDHiResZoom_Off:
				printf("%u - kNKMAIDHiResZoom_Off\n", i);
				break;
			case kNKMAIDHiResZoom_On:
				printf("%u - kNKMAIDHiResZoom_On\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case  kNkMAIDCapability_FocusPointLock:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDFocusPointLock_Disable:
				printf("%u - kNkMAIDFocusPointLock_Disable\n", i);
				break;
			case kNkMAIDFocusPointLock_Enable:
				printf("%u - kNkMAIDFocusPointLock_Enable\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieFocusPointLock:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case     kNkMAIDMovieFocusPointLock_Disable:
				printf("%u -kNkMAIDMovieFocusPointLock_Disable \n", i);
				break;
			case kNkMAIDMovieFocusPointLock_Enable:
				printf("%u - kNkMAIDMovieFocusPointLock_Enable\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case  kNkMAIDCapability_Viewmode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDViewmode_setting:
				printf("%u - kNkMAIDViewmode_setting\n", i);
				break;
			case kNkMAIDViewmode_viewing:
				printf("%u - kNkMAIDViewmode_viewing\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieRecDestination:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovRecDestination2_Slot1:
				printf("%u - Slot1\n", i);
				break;
			case kNkMAIDMovRecDestination2_Slot2:
				printf("%u - Slot2\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ImageColorSpace:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDImageColorSpace_sRGB:
				printf("%u - kNkMAIDImageColorSpace_sRGB\n", i);
				break;
			case kNkMAIDImageColorSpace_AdobeRGB:
				printf("%u - kNkMAIDImageColorSpace_AdobeRGB\n", i);
				break;
			case kNkMAIDImageColorSpace_BT_2100:
				printf("%u - kNkMAIDImageColorSpace_BT_2100\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ChangeMonitorOffStatus:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDChangeMonitorOffStatus_CancelForcedTurnOff:
				printf("%u - kNkMAIDChangeMonitorOffStatus_CancelForcedTurnOff\n", i);
				break;
			case kNkMAIDChangeMonitorOffStatus_ForcedTurnOff:
				printf("%u - kNkMAIDChangeMonitorOffStatus_ForcedTurnOff\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieScreenSize:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieScreenSize8_QFHD_30p: printf("%u - QFHD_30p\n", i); break;
			case kNkMAIDMovieScreenSize8_QFHD_25p: printf("%u - QFHD_25p\n", i); break;
			case kNkMAIDMovieScreenSize8_QFHD_24p: printf("%u - QFHD_24p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_60p: printf("%u - FullHD_60p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_50p: printf("%u - FullHD_50p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_30p: printf("%u - FullHD_30p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_25p: printf("%u - FullHD_25p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_24p: printf("%u - FullHD_24p\n", i); break;
			case kNkMAIDMovieScreenSize8_820p_60p: printf("%u - 820p_60p\n", i); break;
			case kNkMAIDMovieScreenSize8_820p_50p: printf("%u - 820p_50p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_60p_Crop: printf("%u - FullHD_60p_Crop\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_50p_Crop: printf("%u - FullHD_50p_Crop\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_30p_Crop: printf("%u - FullHD_30p_Crop\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_25p_Crop: printf("%u - FullHD_25p_Crop\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_24p_Crop: printf("%u - FullHD_24p_Crop\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_30p_x4_Slow: printf("%u - FullHD_30p_x4_Slow\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_25p_x4_Slow: printf("%u - FullHD_25p_x4_Slow\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_24p_x5_Slow: printf("%u - FullHD_24p_x5_Slow\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_120p: printf("%u - FullHD_120p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_100p: printf("%u - FullHD_100p\n", i); break;
			case kNkMAIDMovieScreenSize8_720p_60p: printf("%u - 720p_60p\n", i); break;
			case kNkMAIDMovieScreenSize8_720p_50p: printf("%u - 720p_50p\n", i); break;
			case kNkMAIDMovieScreenSize8_QFHD_60p: printf("%u - QFHD_60p\n", i); break;
			case kNkMAIDMovieScreenSize8_QFHD_50p: printf("%u - QFHD_50p\n", i); break;
			case kNkMAIDMovieScreenSize8_8256x4644x60p: printf("%u - 8256x4644x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_8256x4644x50p: printf("%u - 8256x4644x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_8256x4644x30p: printf("%u - 8256x4644x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_8256x4644x25p: printf("%u - 8256x4644x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_8256x4644x24p: printf("%u - 8256x4644x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x120p: printf("%u - 4128x2322x120p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x100p: printf("%u - 4128x2322x100p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x60p: printf("%u - 4128x2322x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x50p: printf("%u - 4128x2322x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x30p: printf("%u - 4128x2322x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x25p: printf("%u - 4128x2322x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_4128x2322x24p: printf("%u - 4128x2322x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_5392x3032x60p: printf("%u - 5392x3032x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_5392x3032x50p: printf("%u - 5392x3032x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_5392x3032x30p: printf("%u - 5392x3032x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_5392x3032x25p: printf("%u - 5392x3032x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_5392x3032x24p: printf("%u - 5392x3032x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_7680x4320x30p: printf("%u - 7680x4320x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_7680x4320x25p: printf("%u - 7680x4320x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_7680x4320x24p: printf("%u - 7680x4320x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_3840x2160x120p: printf("%u - 3840x2160x120p\n", i); break;
			case kNkMAIDMovieScreenSize8_3840x2160x100p: printf("%u - 3840x2160x100p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x60p:  printf("%u - 6048x3402x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x50p: printf("%u - 6048x3402x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x30p: printf("%u - 6048x3402x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x25p: printf("%u - 6048x3402x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x24p: printf("%u - 6048x3402x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_4030x2268x60p: printf("%u - 4030x2268x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_4030x2268x50p: printf("%u - 4030x2268x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_4030x2268x30p: printf("%u - 4030x2268x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_4030x2268x25p: printf("%u - 4030x2268x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_4030x2268x24p: printf("%u - 4030x2268x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x120p: printf("%u - 3984x2240x120p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x100p: printf("%u - 3984x2240x100p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x60p: printf("%u - 3984x2240x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x50p: printf("%u - 3984x2240x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x30p: printf("%u - 3984x2240x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x25p: printf("%u - 3984x2240x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x24p: printf("%u - 3984x2240x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x60p: printf("%u - 5376x3024x60p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x50p: printf("%u - 5376x3024x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x30p: printf("%u - 5376x3024x30p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x25p: printf("%u - 5376x3024x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x24p: printf("%u - 5376x3024x24p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_240p: printf("%u - FullHD_240p\n", i); break;
			case kNkMAIDMovieScreenSize8_FullHD_200: printf("%u - FullHD_200p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x59_94p: printf("%u - 5376x3024x59_94p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x29_97p: printf("%u - 5376x3024x29_97p\n", i); break;
			case kNkMAIDMovieScreenSize8_5376x3024x23_976p: printf("%u - 5376x3024x23_976\n", i); break;
			case kNkMAIDMovieScreenSize8_3840x2160x119_88p: printf("%u - 3840x2160x119_88p\n", i); break;
			case kNkMAIDMovieScreenSize8_3840x2160x59_94p: printf("%u - 3840x2160x59_94p\n", i); break;
			case kNkMAIDMovieScreenSize8_3840x2160x29_97p: printf("%u - 3840x2160x29_97p\n", i); break;
			case kNkMAIDMovieScreenSize8_3840x2160x23_976p: printf("%u - 3840x2160x23_976p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x239_76p: printf("%u - 1920x1080x239_76p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x119_88p: printf("%u - 1920x1080x119_88p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x59_94p: printf("%u - 1920x1080x59_94p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x29_97p: printf("%u - 1920x1080x29_97p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x23_976p: printf("%u - 1920x1080x23_976p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x29_97px4_Slow: printf("%u - 1920x1080x29_97px4_Slow\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080x23_976px5_Slow: printf("%u - 1920x1080x23_976px5_Slow\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x59_94p: printf("%u - 6048x3402x59_94p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x29_97p: printf("%u - 6048x3402x29_97p\n", i); break;
			case kNkMAIDMovieScreenSize8_6048x3402x23_976p: printf("%u - 6048x3402x23_976p\n", i); break;
			case kNkMAIDMovieScreenSize8_4032x2268x59_94p: printf("%u - 4032x2268x59_94p\n", i); break;
			case kNkMAIDMovieScreenSize8_4032x2268x50p: printf("%u - 4032x2268x50p\n", i); break;
			case kNkMAIDMovieScreenSize8_4032x2268x29_97p: printf("%u - 4032x2268x29_97p\n", i); break;
			case kNkMAIDMovieScreenSize8_4032x2268x25p: printf("%u - 4032x2268x25p\n", i); break;
			case kNkMAIDMovieScreenSize8_4032x2268x23_976p: printf("%u - 4032x2268x23_976p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x119_88p: printf("%u - 3984x2240x119_88p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x59_94p: printf("%u - 3984x2240x59_94p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x29_97p: printf("%u - 3984x2240x29_97p\n", i); break;
			case kNkMAIDMovieScreenSize8_3984x2240x23_976p: printf("%u - 3984x2240x23_976p\n", i); break;
			case kNkMAIDMovieScreenSize8_1920x1080_25p_x4_Slow: printf("%u - 1920x1080_25p_x4_Slow\n", i); break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_PictureControl:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDPictureControl_Undefined:
				printf("%u - kNkMAIDPictureControl_Undefined\n", i);
				break;
			case kNkMAIDPictureControl_Standard:
				printf("%u - kNkMAIDPictureControl_Standard\n", i);
				break;
			case kNkMAIDPictureControl_Neutral:
				printf("%u - kNkMAIDPictureControl_Neutral\n", i);
				break;
			case kNkMAIDPictureControl_Vivid:
				printf("%u - kNkMAIDPictureControl_Vivid\n", i);
				break;
			case kNkMAIDPictureControl_Monochrome:
				printf("%u - kNkMAIDPictureControl_Monochrome\n", i);
				break;
			case kNkMAIDPictureControl_Portrait:
				printf("%u - kNkMAIDPictureControl_Portrait\n", i);
				break;
			case kNkMAIDPictureControl_Landscape:
				printf("%u - kNkMAIDPictureControl_Landscape\n", i);
				break;
			case kNkMAIDPictureControl_Flat:
				printf("%u - kNkMAIDPictureControl_Flat\n", i);
				break;
			case kNkMAIDPictureControl_Auto:
				printf("%u - kNkMAIDPictureControl_Auto\n", i);
				break;
			case kNkMAIDPictureControl_Flat_Monochrome:
				printf("%u - kNkMAIDPictureControl_Flat_Monochrome\n", i);
				break;
			case kNkMAIDPictureControl_Deep_Tone_Monochrome:
				printf("%u - kNkMAIDPictureControl_Deep_Tone_Monochrome\n", i);
				break;
			case kNkMAIDPictureControl_Rich_Tone_Portrait:
				printf("%u - kNkMAIDPictureControl_Rich_Tone_Portrait\n", i);
				break;
			case kNkMAIDPictureControl_Dream:
				printf("%u - kNkMAIDPictureControl_Dream\n", i);
				break;
			case kNkMAIDPictureControl_Morning:
				printf("%u - kNkMAIDPictureControl_Morning\n", i);
				break;
			case kNkMAIDPictureControl_Pop:
				printf("%u - kNkMAIDPictureControl_Pop\n", i);
				break;
			case kNkMAIDPictureControl_Sunday:
				printf("%u - kNkMAIDPictureControl_Sunday\n", i);
				break;
			case kNkMAIDPictureControl_Somber:
				printf("%u - kNkMAIDPictureControl_Somber\n", i);
				break;
			case kNkMAIDPictureControl_Dramatic:
				printf("%u - kNkMAIDPictureControl_Dramatic\n", i);
				break;
			case kNkMAIDPictureControl_Silence:
				printf("%u - kNkMAIDPictureControl_Silence\n", i);
				break;
			case kNkMAIDPictureControl_Breached:
				printf("%u - kNkMAIDPictureControl_Breached\n", i);
				break;
			case kNkMAIDPictureControl_Melancholic:
				printf("%u - kNkMAIDPictureControl_Melancholic\n", i);
				break;
			case kNkMAIDPictureControl_Pure:
				printf("%u - kNkMAIDPictureControl_Pure\n", i);
				break;
			case kNkMAIDPictureControl_Denim:
				printf("%u - kNkMAIDPictureControl_Denim\n", i);
				break;
			case kNkMAIDPictureControl_Toy:
				printf("%u - kNkMAIDPictureControl_Toy\n", i);
				break;
			case kNkMAIDPictureControl_Sepia:
				printf("%u - kNkMAIDPictureControl_Sepia\n", i);
				break;
			case kNkMAIDPictureControl_Blue:
				printf("%u - kNkMAIDPictureControl_Blue\n", i);
				break;
			case kNkMAIDPictureControl_Red:
				printf("%u - kNkMAIDPictureControl_Red\n", i);
				break;
			case kNkMAIDPictureControl_Pink:
				printf("%u - kNkMAIDPictureControl_Pink\n", i);
				break;
			case kNkMAIDPictureControl_Charcoal:
				printf("%u - kNkMAIDPictureControl_Charcoal\n", i);
				break;
			case kNkMAIDPictureControl_Graphite:
				printf("%u - kNkMAIDPictureControl_Graphite\n", i);
				break;
			case kNkMAIDPictureControl_Binary:
				printf("%u - kNkMAIDPictureControl_Binary\n", i);
				break;
			case kNkMAIDPictureControl_Carbon:
				printf("%u - kNkMAIDPictureControl_Carbon\n", i);
				break;
			case kNkMAIDPictureControl_Custom1:
				printf("%u - kNkMAIDPictureControl_Custom1\n", i);
				break;
			case kNkMAIDPictureControl_Custom2:
				printf("%u - kNkMAIDPictureControl_Custom2\n", i);
				break;
			case kNkMAIDPictureControl_Custom3:
				printf("%u - kNkMAIDPictureControl_Custom3\n", i);
				break;
			case kNkMAIDPictureControl_Custom4:
				printf("%u - kNkMAIDPictureControl_Custom4\n", i);
				break;
			case kNkMAIDPictureControl_Custom5:
				printf("%u - kNkMAIDPictureControl_Custom5\n", i);
				break;
			case kNkMAIDPictureControl_Custom6:
				printf("%u - kNkMAIDPictureControl_Custom6\n", i);
				break;
			case kNkMAIDPictureControl_Custom7:
				printf("%u - kNkMAIDPictureControl_Custom7\n", i);
				break;
			case kNkMAIDPictureControl_Custom8:
				printf("%u - kNkMAIDPictureControl_Custom8\n", i);
				break;
			case kNkMAIDPictureControl_Custom9:
				printf("%u - kNkMAIDPictureControl_Custom9\n", i);
				break;
			case kNkMAIDPictureControl_Cloud1:
				printf("%u - kNkMAIDPictureControl_Cloud1\n", i);
				break;
			case kNkMAIDPictureControl_Cloud2:
				printf("%u - kNkMAIDPictureControl_Cloud2\n", i);
				break;
			case kNkMAIDPictureControl_Cloud3:
				printf("%u - kNkMAIDPictureControl_Cloud3\n", i);
				break;
			case kNkMAIDPictureControl_Cloud4:
				printf("%u - kNkMAIDPictureControl_Cloud4\n", i);
				break;
			case kNkMAIDPictureControl_Cloud5:
				printf("%u - kNkMAIDPictureControl_Cloud5\n", i);
				break;
			case kNkMAIDPictureControl_Cloud6:
				printf("%u - kNkMAIDPictureControl_Cloud6\n", i);
				break;
			case kNkMAIDPictureControl_Cloud7:
				printf("%u - kNkMAIDPictureControl_Cloud7\n", i);
				break;
			case kNkMAIDPictureControl_Cloud8:
				printf("%u - kNkMAIDPictureControl_Cloud8\n", i);
				break;
			case kNkMAIDPictureControl_Cloud9:
				printf("%u - kNkMAIDPictureControl_Cloud9\n", i);
				break;
			default:
				printf("Invalid value returned\n");
				return FALSE;
			}
		}
	}
	break;
	case kNkMAIDCapability_MoviePictureControl:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMoviePictureControl_Undefined:
				printf("%u - kNkMAIDMoviePictureControl_Undefined\n", i);
				break;
			case kNkMAIDMoviePictureControl_Standard:
				printf("%u - kNkMAIDMoviePictureControl_Standard\n", i);
				break;
			case kNkMAIDMoviePictureControl_Neutral:
				printf("%u - kNkMAIDMoviePictureControl_Neutral\n", i);
				break;
			case kNkMAIDMoviePictureControl_Vivid:
				printf("%u - kNkMAIDMoviePictureControl_Vivid\n", i);
				break;
			case kNkMAIDMoviePictureControl_Monochrome:
				printf("%u - kNkMAIDMoviePictureControl_Monochrome\n", i);
				break;
			case kNkMAIDMoviePictureControl_Portrait:
				printf("%u - kNkMAIDMoviePictureControl_Portrait\n", i);
				break;
			case kNkMAIDMoviePictureControl_Landscape:
				printf("%u - kNkMAIDMoviePictureControl_Landscape\n", i);
				break;
			case kNkMAIDMoviePictureControl_Flat:
				printf("%u - kNkMAIDMoviePictureControl_Flat\n", i);
				break;
			case kNkMAIDMoviePictureControl_Auto:
				printf("%u - kNkMAIDMoviePictureControl_Auto\n", i);
				break;
			case kNkMAIDMoviePictureControl_Flat_Monochrome:
				printf("%u - kNkMAIDMoviePictureControl_Flat_Monochrome\n", i);
				break;
			case kNkMAIDMoviePictureControl_Deep_Tone_Monochrome:
				printf("%u - kNkMAIDMoviePictureControl_Deep_Tone_Monochrome\n", i);
				break;
			case kNkMAIDMoviePictureControl_Rich_Tone_Portrait:
				printf("%u - kNkMAIDMoviePictureControl_Rich_Tone_Portrait\n", i);
				break;
			case kNkMAIDMoviePictureControl_SamePhoto:
				printf("%u - kNkMAIDMoviePictureControl_SamePhoto\n", i);
				break;
			case kNkMAIDMoviePictureControl_Dream:
				printf("%u - kNkMAIDMoviePictureControl_Dream\n", i);
				break;
			case kNkMAIDMoviePictureControl_Morning:
				printf("%u - kNkMAIDMoviePictureControl_Morning\n", i);
				break;
			case kNkMAIDMoviePictureControl_Pop:
				printf("%u - kNkMAIDMoviePictureControl_Pop\n", i);
				break;
			case kNkMAIDMoviePictureControl_Sunday:
				printf("%u - kNkMAIDMoviePictureControl_Sunday\n", i);
				break;
			case kNkMAIDMoviePictureControl_Somber:
				printf("%u - kNkMAIDMoviePictureControl_Somber\n", i);
				break;
			case kNkMAIDMoviePictureControl_Dramatic:
				printf("%u - kNkMAIDMoviePictureControl_Dramatic\n", i);
				break;
			case kNkMAIDMoviePictureControl_Silence:
				printf("%u - kNkMAIDMoviePictureControl_Silence\n", i);
				break;
			case kNkMAIDMoviePictureControl_Breached:
				printf("%u - kNkMAIDMoviePictureControl_Breached\n", i);
				break;
			case kNkMAIDMoviePictureControl_Melancholic:
				printf("%u - kNkMAIDMoviePictureControl_Melancholic\n", i);
				break;
			case kNkMAIDMoviePictureControl_Pure:
				printf("%u - kNkMAIDMoviePictureControl_Pure\n", i);
				break;
			case kNkMAIDMoviePictureControl_Denim:
				printf("%u - kNkMAIDMoviePictureControl_Denim\n", i);
				break;
			case kNkMAIDMoviePictureControl_Toy:
				printf("%u - kNkMAIDMoviePictureControl_Toy\n", i);
				break;
			case kNkMAIDMoviePictureControl_Sepia:
				printf("%u - kNkMAIDMoviePictureControl_Sepia\n", i);
				break;
			case kNkMAIDMoviePictureControl_Blue:
				printf("%u - kNkMAIDMoviePictureControl_Blue\n", i);
				break;
			case kNkMAIDMoviePictureControl_Red:
				printf("%u - kNkMAIDMoviePictureControl_Red\n", i);
				break;
			case kNkMAIDMoviePictureControl_Pink:
				printf("%u - kNkMAIDMoviePictureControl_Pink\n", i);
				break;
			case kNkMAIDMoviePictureControl_Charcoal:
				printf("%u - kNkMAIDMoviePictureControl_Charcoal\n", i);
				break;
			case kNkMAIDMoviePictureControl_Graphite:
				printf("%u - kNkMAIDMoviePictureControl_Graphite\n", i);
				break;
			case kNkMAIDMoviePictureControl_Binary:
				printf("%u - kNkMAIDMoviePictureControl_Binary\n", i);
				break;
			case kNkMAIDMoviePictureControl_Carbon:
				printf("%u - kNkMAIDMoviePictureControl_Carbon\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom1:
				printf("%u - kNkMAIDMoviePictureControl_Custom1\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom2:
				printf("%u - kNkMAIDMoviePictureControl_Custom2\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom3:
				printf("%u - kNkMAIDMoviePictureControl_Custom3\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom4:
				printf("%u - kNkMAIDMoviePictureControl_Custom4\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom5:
				printf("%u - kNkMAIDMoviePictureControl_Custom5\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom6:
				printf("%u - kNkMAIDMoviePictureControl_Custom6\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom7:
				printf("%u - kNkMAIDMoviePictureControl_Custom7\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom8:
				printf("%u - kNkMAIDMoviePictureControl_Custom8\n", i);
				break;
			case kNkMAIDMoviePictureControl_Custom9:
				printf("%u - kNkMAIDMoviePictureControl_Custom9\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud1:
				printf("%u - kNkMAIDMoviePictureControl_Cloud1\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud2:
				printf("%u - kNkMAIDMoviePictureControl_Cloud2\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud3:
				printf("%u - kNkMAIDMoviePictureControl_Cloud3\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud4:
				printf("%u - kNkMAIDMoviePictureControl_Cloud4\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud5:
				printf("%u - kNkMAIDMoviePictureControl_Cloud5\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud6:
				printf("%u - kNkMAIDMoviePictureControl_Cloud6\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud7:
				printf("%u - kNkMAIDMoviePictureControl_Cloud7\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud8:
				printf("%u - kNkMAIDMoviePictureControl_Cloud8\n", i);
				break;
			case kNkMAIDMoviePictureControl_Cloud9:
				printf("%u - kNkMAIDMoviePictureControl_Cloud9\n", i);
				break;
			default:
				printf("Invalid value returned\n");
				return FALSE;
			}
		}
	}
	break;
	case kNkMAIDCapability_PictureControlHlg:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDPictureControlHlg_Standard:
				printf("%u - Standard\n", i);
				break;
			case kNkMAIDPictureControlHlg_Monochrome:
				printf("%u - Monochrome\n", i);
				break;
			case kNkMAIDPictureControlHlg_Flat:
				printf("%u - Flat\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieH265ToneMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDToneMode_SDR:
				printf("%u - SDR\n", i);
				break;
			case kNkMAIDToneMode_NLOG:
				printf("%u - NLOG\n", i);
				break;
			case kNkMAIDToneMode_HLG:
				printf("%u - HLG\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ElectronicFrontCurtainShutterEx:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDElectronicFrontCurtainShutter_Off:
				printf("%u - Off\n", i);
				break;
			case kNkMAIDElectronicFrontCurtainShutter_On:
				printf("%u - On\n", i);
				break;
			case kNkMAIDElectronicFrontCurtainShutter_Auto:
				printf("%u - Auto\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_MovieMeteringMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieMeteringMode_Matrix:
				printf("%u - Matrix\n", i);
				break;

			case kNkMAIDMovieMeteringMode_CenterWeighted:
				printf("%u -CenterWeighted\n", i);
				break;

			case kNkMAIDMovieMeteringMode_HighLight:
				printf("%u -HighLight\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_MovieCCDDataMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieCCDDataMode_FXFormat:
				printf("%u - FXFormat\n", i);
				break;

			case kNkMAIDMovieCCDDataMode_DXFormat:
				printf("%u -DXFormat\n", i);
				break;

			case kNkMAIDMovieCCDDataMode_13x:
				printf("%u -13x\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MeteringMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMeteringMode_Matrix:
				printf("%u - Matrix\n", i);
				break;

			case kNkMAIDMeteringMode_CenterWeighted:
				printf("%u -CenterWeighted\n", i);
				break;

			case kNkMAIDMeteringMode_Spot:
				printf("%u -Spot\n", i);
				break;

			case kNkMAIDMeteringMode_AfSpot:
				printf("%u -AfSpot\n", i);
				break;

			case kNkMAIDMeteringMode_HighLight:
				printf("%u -HighLight\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieActive_D_Lighting:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieActive_D_Lighting_Off:
				printf("%u - Off\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_Low:
				printf("%u -Low\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_Normal:
				printf("%u -Normal\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_High:
				printf("%u -High\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_ExtraHigh:
				printf("%u -ExtraHigh\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_SamePhoto:
				printf("%u -SamePhoto\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_ExtraHigh1:
				printf("%u -ExtraHigh1\n", i);
				break;

			case kNkMAIDMovieActive_D_Lighting_ExtraHigh2:
				printf("%u -ExtraHigh2\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieAfAreaMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eMovieAfAreaMode_Single:
				printf("%u - Single\n", i);
				break;

			case eMovieAfAreaMode_Auto:
				printf("%u - Auto\n", i);
				break;

			case eMovieAfAreaMode_WideArea_S:
				printf("%u -WideArea_S\n", i);
				break;

			case eMovieAfAreaMode_WideArea_L:
				printf("%u -WideArea_L\n", i);
				break;

			case eMovieAfAreaMode_FaceDetection:
				printf("%u - FaceDetection\n", i);
				break;

			case eMovieAfAreaMode_NomalArea:
				printf("%u -NomalArea\n", i);
				break;

			case eMovieAfAreaMode_TargetTracking:
				printf("%u - TargetTracking\n", i);
				break;

			case eMovieAfAreaMode_Auto_Animals:
				printf("%u -Auto_Animals\n", i);
				break;

			case eMovieAfAreaMode_Auto_People:
				printf("%u -Auto_People\n", i);
				break;

			case eMovieAfAreaMode_WideArea_L_Animals:
				printf("%u -WideArea_L_Animals\n", i);
				break;

			case eMovieAfAreaMode_WideArea_L_People:
				printf("%u -WideArea_L_People\n", i);
				break;

			case eMovieAfAreaMode_WideArea:
				printf("%u -WideArea\n", i);
				break;

			case eMovieAfAreaMode_c1:
				printf("%u -C1\n", i);
				break;

			case eMovieAfAreaMode_c2:
				printf("%u -C2\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_FocusAreaMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eFocusAreaMode_Single:
				printf("%u - Single\n", i);
				break;

			case eFocusAreaMode_Auto:
				printf("%u - Auto\n", i);
				break;

			case eFocusAreaMode_Pinpoint:
				printf("%u -Pinpoint\n", i);
				break;

			case eFocusAreaMode_WideArea_S:
				printf("%u -WideArea_S\n", i);
				break;

			case eFocusAreaMode_WideArea_L:
				printf("%u -WideArea_L\n", i);
				break;

			case eFocusAreaMode_Dynamic:
				printf("%u - Dynamic\n", i);
				break;

			case eFocusAreaMode_Dynamic_9p:
				printf("%u -Dynamic_9p\n", i);
				break;

			case eFocusAreaMode_Dynamic_105p:
				printf("%u - Dynamic_105p\n", i);
				break;

			case eFocusAreaMode_Dynamic_49p:
				printf("%u -Dynamic_49p\n", i);
				break;

			case eFocusAreaMode_Dynamic_25p:
				printf("%u -Dynamic_25p\n", i);
				break;

			case eFocusAreaMode_Dynamic_51p:
				printf("%u -Dynamic_51p\n", i);
				break;

			case eFocusAreaMode_Dynamic_21p:
				printf("%u -Dynamic_21p\n", i);
				break;

			case eFocusAreaMode_3DTracking:
				printf("%u -3DTracking\n", i);
				break;

			case eFocusAreaMode_WideArea_C1:
				printf("%u -WideArea_C1\n", i);
				break;

			case eFocusAreaMode_WideArea_C2:
				printf("%u -WideArea_C2\n", i);
				break;

			case eFocusAreaMode_Auto_Animals:
				printf("%u -Auto_Animals\n", i);
				break;

			case eFocusAreaMode_Auto_People:
				printf("%u -Auto_People\n", i);
				break;

			case eFocusAreaMode_WideArea_L_Animals:
				printf("%u -WideArea_L_Animals\n", i);
				break;

			case eFocusAreaMode_WideArea_L_People:
				printf("%u -WideArea_L_People\n", i);
				break;

			case eFocusAreaMode_Group_C1:
				printf("%u -Group_C1\n", i);
				break;

			case eFocusAreaMode_Group_C2:
				printf("%u -Group_C2\n", i);
				break;

			case eFocusAreaMode_Group:
				printf("%u -Group\n", i);
				break;

			case eFocusAreaMode_FaceDetection:
				printf("%u -FaceDetection\n", i);
				break;

			case eFocusAreaMode_WideArea:
				printf("%u -WideArea\n", i);
				break;

			case eFocusAreaMode_NomalArea:
				printf("%u -NomalArea\n", i);
				break;

			case eFocusAreaMode_TargetTracking:
				printf("%u -TargetTracking\n", i);
				break;

			case eFocusAreaMode_Dynamic_S:
				printf("%u -Dynamic_S\n", i);
				break;

			case eFocusAreaMode_Dynamic_M:
				printf("%u -Dynamic_M\n", i);
				break;

			case eFocusAreaMode_Dynamic_L:
				printf("%u -Dynamic_L\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_FocusMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDFocusMode_MF:
				printf("%u - MF\n", i);
				break;

			case kNkMAIDFocusMode_AFs:
				printf("%u -AFs\n", i);
				break;

			case kNkMAIDFocusMode_AFc:
				printf("%u -AFc\n", i);
				break;

			case kNkMAIDFocusMode_AFa:
				printf("%u -AFa\n", i);
				break;

			case kNkMAIDFocusMode_AFf:
				printf("%u -AFf\n", i);
				break;

			case kNkMAIDFocusMode_AF:
				printf("%u -AF\n", i);
				break;

			case kNkMAIDFocusMode_Macro:
				printf("%u -Macro\n", i);
				break;

			case kNkMAIDFocusMode_Infinity:
				printf("%u -Infinity\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_CompressRAWEx:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDCompressRAWEx_Uncompressed:
				printf("%u - Uncompressed\n", i);
				break;

			case kNkMAIDCompressRAWEx_Compressed:
				printf("%u -Compressed\n", i);
				break;

			case kNkMAIDCompressRAWEx_LosslessCompressed:
				printf("%u -LosslessCompressed\n", i);
				break;

			case kNkMAIDCompressRAWEx_Highefficiency_1:
				printf("%u -Highefficiency_1\n", i);
				break;

			case kNkMAIDCompressRAWEx_Highefficiency:
				printf("%u -Highefficiency\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_AFSubjectDetection:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDAFSubjectDetection_None:
				printf("%u - None\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Auto:
				printf("%u -Auto\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Person:
				printf("%u - Person\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Vehicle:
				printf("%u - Vehicle\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Animal:
				printf("%u -Animal\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Bird:
				printf("%u - Bird\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Airplane:
				printf("%u -Airplane\n", i);
				break;
			case kNkMAIDAFSubjectDetection_Train:
				printf("%u -Train\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_MovieAFSubjectDetection:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieAFSubjectDetection_None:
				printf("%u - None\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Auto:
				printf("%u -Auto\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Person:
				printf("%u - Person\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Vehicle:
				printf("%u - Vehicle\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Animal:
				printf("%u -Animal\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Bird:
				printf("%u - Bird\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Airplane:
				printf("%u -Airplane\n", i);
				break;
			case kNkMAIDMovieAFSubjectDetection_Train:
				printf("%u -Train\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_MovieImageQuality:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieImageQuality_Normal:
				printf("%u - Normal\n", i);
				break;
			case kNkMAIDMovieImageQuality_Fine:
				printf("%u -Fine\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_ExternalRecordingControl:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDExternalRecordingControl_Off:
				printf("%u - Off\n", i);
				break;
			case kNkMAIDExternalRecordingControl_On:
				printf("%u - On\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;;
			}
		}
	}
	break;
	case kNkMAIDCapability_HighlightBrightness:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDHighlightBrightness_180:
				printf("%u - kNkMAIDHighlightBrightness_180\n", i);
				break;
			case kNkMAIDHighlightBrightness_191:
				printf("%u - kNkMAIDHighlightBrightness_191\n", i);
				break;
			case kNkMAIDHighlightBrightness_202:
				printf("%u - kNkMAIDHighlightBrightness_202\n", i);
				break;
			case kNkMAIDHighlightBrightness_213:
				printf("%u - kNkMAIDHighlightBrightness_213\n", i);
				break;
			case kNkMAIDHighlightBrightness_224:
				printf("%u - kNkMAIDHighlightBrightness_224\n", i);
				break;
			case kNkMAIDHighlightBrightness_235:
				printf("%u - kNkMAIDHighlightBrightness_235\n", i);
				break;
			case kNkMAIDHighlightBrightness_248:
				printf("%u - kNkMAIDHighlightBrightness_248\n", i);
				break;
			case kNkMAIDHighlightBrightness_255:
				printf("%u - kNkMAIDHighlightBrightness_255\n", i);
				break;
			case kNkMAIDHighlightBrightness_120:
				printf("%u - kNkMAIDHighlightBrightness_120\n", i);
				break;
			case kNkMAIDHighlightBrightness_125:
				printf("%u - kNkMAIDHighlightBrightness_125\n", i);
				break;
			case kNkMAIDHighlightBrightness_130:
				printf("%u - kNkMAIDHighlightBrightness_130\n", i);
				break;
			case kNkMAIDHighlightBrightness_135:
				printf("%u - kNkMAIDHighlightBrightness_135\n", i);
				break;
			case kNkMAIDHighlightBrightness_140:
				printf("%u - kNkMAIDHighlightBrightness_140\n", i);
				break;
			case kNkMAIDHighlightBrightness_145:
				printf("%u - kNkMAIDHighlightBrightness_145\n", i);
				break;
			case kNkMAIDHighlightBrightness_150:
				printf("%u - kNkMAIDHighlightBrightness_150\n", i);
				break;
			case kNkMAIDHighlightBrightness_155:
				printf("%u - kNkMAIDHighlightBrightness_155\n", i);
				break;
			case kNkMAIDHighlightBrightness_160:
				printf("%u - kNkMAIDHighlightBrightness_160\n", i);
				break;
			case kNkMAIDHighlightBrightness_165:
				printf("%u - kNkMAIDHighlightBrightness_165\n", i);
				break;
			case kNkMAIDHighlightBrightness_170:
				printf("%u - kNkMAIDHighlightBrightness_170\n", i);
				break;
			case kNkMAIDHighlightBrightness_175:
				printf("%u - kNkMAIDHighlightBrightness_175\n", i);
				break;
			case kNkMAIDHighlightBrightness_185:
				printf("%u - kNkMAIDHighlightBrightness_185\n", i);
				break;
			case kNkMAIDHighlightBrightness_190:
				printf("%u - kNkMAIDHighlightBrightness_190\n", i);
				break;
			case kNkMAIDHighlightBrightness_195:
				printf("%u - kNkMAIDHighlightBrightness_195\n", i);
				break;
			case kNkMAIDHighlightBrightness_200:
				printf("%u - kNkMAIDHighlightBrightness_200\n", i);
				break;
			case kNkMAIDHighlightBrightness_205:
				printf("%u - kNkMAIDHighlightBrightness_205\n", i);
				break;
			case kNkMAIDHighlightBrightness_210:
				printf("%u - kNkMAIDHighlightBrightness_210\n", i);
				break;
			case kNkMAIDHighlightBrightness_215:
				printf("%u - kNkMAIDHighlightBrightness_215\n", i);
				break;
			case kNkMAIDHighlightBrightness_220:
				printf("%u - kNkMAIDHighlightBrightness_220\n", i);
				break;
			case kNkMAIDHighlightBrightness_225:
				printf("%u - kNkMAIDHighlightBrightness_225\n", i);
				break;
			case kNkMAIDHighlightBrightness_230:
				printf("%u - kNkMAIDHighlightBrightness_230\n", i);
				break;
			case kNkMAIDHighlightBrightness_240:
				printf("%u - kNkMAIDHighlightBrightness_240\n", i);
				break;
			case kNkMAIDHighlightBrightness_245:
				printf("%u - kNkMAIDHighlightBrightness_245\n", i);
				break;
			case kNkMAIDHighlightBrightness_250:
				printf("%u - kNkMAIDHighlightBrightness_250\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_VibrationReduction:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDVibrationReduction_Off:
				printf("%u - kNkMAIDVibrationReduction_Off\n", i);
				break;

			case kNkMAIDVibrationReduction_Normal:
				printf("%u - kNkMAIDVibrationReduction_Normal\n", i);
				break;

			case kNkMAIDVibrationReduction_Sport:
				printf("%u - kNkMAIDVibrationReduction_Sport\n", i);
				break;


			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_Active_D_Lighting:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDActive_D_Lighting_High:
				printf("%u - kNkMAIDActive_D_Lighting_High\n", i);
				break;

			case kNkMAIDActive_D_Lighting_Normal:
				printf("%u - kNkMAIDActive_D_Lighting_Normal\n", i);
				break;

			case kNkMAIDActive_D_Lighting_Low:
				printf("%u - kNkMAIDActive_D_Lighting_Low\n", i);
				break;
			case kNkMAIDActive_D_Lighting_Off:
				printf("%u - kNkMAIDActive_D_Lighting_Off\n", i);
				break;
			case kNkMAIDActive_D_Lighting_On:
				printf("%u - kNkMAIDActive_D_Lighting_On\n", i);
				break;
			case kNkMAIDActive_D_Lighting_ExtraHigh:
				printf("%u - kNkMAIDActive_D_Lighting_ExtraHigh\n", i);
				break;
			case kNkMAIDActive_D_Lighting_Auto:
				printf("%u - kNkMAIDActive_D_Lighting_Auto\n", i);
				break;
			case kNkMAIDActive_D_Lighting_ExtraHigh2:
				printf("%u - kNkMAIDActive_D_Lighting_ExtraHigh2\n", i);
				break;
			case kNkMAIDActive_D_Lighting_ExtraSingleHigh:
				printf("%u - kNkMAIDActive_D_Lighting_ExtraSingleHigh (Extrahigh1)\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_Slot2ImageSaveMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDSlot2ImageSaveMode_Overflow:
				printf("%u - Overflow\n", i);
				break;

			case kNkMAIDSlot2ImageSaveMode_Backup:
				printf("%u - Backup\n", i);
				break;

			case kNkMAIDSlot2ImageSaveMode_Jpeg:
				printf("%u - RAW primary & JPEG secondary\n", i);
				break;
			case kNkMAIDSlot2ImageSaveMode_SplitlJpeg:
				printf("%u - Jpeg & Smaller Jpeg\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_CCDDataMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDCCDDataMode_Full:
				printf("%u - kNkMAIDCCDDataMode_Full\n", i);
				break;

			case kNkMAIDCCDDataMode_HiSpeedCrop:
				printf("%u - kNkMAIDCCDDataMode_HiSpeedCrop\n", i);
				break;

			case kNkMAIDCCDDataMode_AutoDXCrop:
				printf("%u - kNkMAIDCCDDataMode_AutoDXCrop\n", i);
				break;
			case kNkMAIDCCDDataMode_FXFormat:
				printf("%u - kNkMAIDCCDDataMode_FXFormat\n", i);
				break;

			case kNkMAIDCCDDataMode_DXFormat:
				printf("%u - kNkMAIDCCDDataMode_DXFormat\n", i);
				break;

			case kNkMAIDCCDDataMode_5_4:
				printf("%u - kNkMAIDCCDDataMode_5_4\n", i);
				break;
			case kNkMAIDCCDDataMode_12x:
				printf("%u - kNkMAIDCCDDataMode_12x\n", i);
				break;

			case kNkMAIDCCDDataMode_13x:
				printf("%u - kNkMAIDCCDDataMode_13x\n", i);
				break;

			case kNkMAIDCCDDataMode_1_1:
				printf("%u - kNkMAIDCCDDataMode_1_1\n", i);
				break;

			case kNkMAIDCCDDataMode_16_9:
				printf("%u - kNkMAIDCCDDataMode_16_9\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ADLBracketingStep:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDADLBracketingStep_Auto:
				printf("%u - kNkMAIDADLBracketingStep_Auto\n", i);
				break;

			case kNkMAIDADLBracketingStep_Low:
				printf("%u - kNkMAIDADLBracketingStep_Low\n", i);
				break;

			case kNkMAIDADLBracketingStep_Normal:
				printf("%u - kNkMAIDADLBracketingStep_Normal\n", i);
				break;
			case kNkMAIDADLBracketingStep_High:
				printf("%u - kNkMAIDADLBracketingStep_High\n", i);
				break;

			case kNkMAIDADLBracketingStep_ExtraHigh_1:
				printf("%u - kNkMAIDADLBracketingStep_ExtraHigh_1\n", i);
				break;

			case kNkMAIDADLBracketingStep_ExtraHigh_2:
				printf("%u - kNkMAIDADLBracketingStep_ExtraHigh_2\n", i);
				break;

			case kNkMAIDADLBracketingStep_ExtraHighPlus:
				printf("%u - kNkMAIDADLBracketingStep_ExtraHighPlus\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ADLBracketingType:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDADLBracketingType_2:
				printf("%u - kNkMAIDADLBracketingType_2\n", i);
				break;

			case kNkMAIDADLBracketingType_3:
				printf("%u - kNkMAIDADLBracketingType_3\n", i);
				break;

			case kNkMAIDADLBracketingType_4:
				printf("%u - kNkMAIDADLBracketingType_4\n", i);
				break;
			case kNkMAIDADLBracketingType_5:
				printf("%u - kNkMAIDADLBracketingType_5\n", i);
				break;

			case kNkMAIDADLBracketingType_5_Max_ExHi2:
				printf("%u - kNkMAIDADLBracketingType_5_Max_ExHi2\n", i);
				break;

			case kNkMAIDADLBracketingType_0:
				printf("%u - kNkMAIDADLBracketingType_0\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_BracketingType:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eNkMAIDBracketingType_Minus_2:
				printf("%u - eNkMAIDBracketingType_Minus_2\n", i);
				break;

			case eNkMAIDBracketingType_Puls_2:
				printf("%u - eNkMAIDBracketingType_Puls_2\n", i);
				break;

			case eNkMAIDBracketingType_Minus_3:
				printf("%u - eNkMAIDBracketingType_Minus_3\n", i);
				break;

			case eNkMAIDBracketingType_Puls_3:
				printf("%u - eNkMAIDBracketingType_Puls_3\n", i);
				break;

			case eNkMAIDBracketingType_Both_3:
				printf("%u - eNkMAIDBracketingType_Both_3\n", i);
				break;

			case eNkMAIDBracketingType_Both_5:
				printf("%u - eNkMAIDBracketingType_Both_5\n", i);
				break;

			case eNkMAIDBracketingType_Both_7:
				printf("%u - eNkMAIDBracketingType_Both_7\n", i);
				break;

			case eNkMAIDBracketingType_Both_9:
				printf("%u - eNkMAIDBracketingType_Both_9\n", i);
				break;

			case eNkMAIDBracketingType_None_0:
				printf("%u - eNkMAIDBracketingType_None_0\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_WBBracketingStep:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eNkMAIDWBBracketingStep_1STEP:
				printf("%u - eNkMAIDWBBracketingStep_1STEP\n", i);
				break;

			case eNkMAIDWBBracketingStep_2STEP:
				printf("%u - eNkMAIDWBBracketingStep_2STEP\n", i);
				break;

			case eNkMAIDWBBracketingStep_3STEP:
				printf("%u - eNkMAIDWBBracketingStep_3STEP\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_AEBracketingStep:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eNkMAIDAEBracketingStep_1_3EV:
				printf("%u - eNkMAIDAEBracketingStep_1_3EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_1_2EV:
				printf("%u - eNkMAIDAEBracketingStep_1_2EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_2_3EV:
				printf("%u - eNkMAIDAEBracketingStep_2_3EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_1EV:
				printf("%u - eNkMAIDAEBracketingStep_1EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_4_3EV:
				printf("%u - eNkMAIDAEBracketingStep_4_3EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_3_2EV:
				printf("%u - eNkMAIDAEBracketingStep_3_2EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_5_3EV:
				printf("%u - eNkMAIDAEBracketingStep_5_3EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_2EV:
				printf("%u - eNkMAIDAEBracketingStep_2EV\n", i);
				break;

			case eNkMAIDAEBracketingStep_3EV:
				printf("%u - eNkMAIDAEBracketingStep_3EV\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_AFModeAtLiveView:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDAFModeAtLiveView_S:
				printf("%u - AFModeAtLiveView_S\n", i);
				break;

			case kNkMAIDAFModeAtLiveView_C:
				printf("%u - AFModeAtLiveView_C\n", i);
				break;

			case kNkMAIDAFModeAtLiveView_F:
				printf("%u - AFModeAtLiveView_F\n", i);
				break;

			case kNkMAIDAFModeAtLiveView_M_FIX:
				printf("%u - AFModeAtLiveView_M_FIX\n", i);
				break;

			case kNkMAIDAFModeAtLiveView_M_SEL:
				printf("%u - AFModeAtLiveView_M_SEL\n", i);
				break;

			case kNkMAIDAFModeAtLiveView_A:
				printf("%u - AFModeAtLiveView_A\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_MovieWBFluorescentType:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{

			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMovieWBFluorescentType_SodiumVapor:
				printf("%u - SodiumVapor\n", i);
				break;
			case kNkMovieWBFluorescentType_WarmWhite:
				printf("%u - WarmWhite\n", i);
				break;
			case kNkMovieWBFluorescentType_White:
				printf("%u - White\n", i);
				break;
			case kNkMovieWBFluorescentType_CoolWhite:
				printf("%u - CoolWhite\n", i);
				break;
			case kNkMovieWBFluorescentType_DayWhite:
				printf("%u - DayWhite\n", i);
				break;
			case kNkMovieWBFluorescentType_Daylight:
				printf("%u - Daylight\n", i);
				break;
			case kNkMovieWBFluorescentType_HiTempMercuryVapor:
				printf("%u - HiTempMercuryVapor\n", i);
				break;

			}
		}
	}
	break;
	case kNkMAIDCapability_WBFluorescentType:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{

			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkWBFluorescentType_SodiumVapor:
				printf("%u - SodiumVapor\n", i);
				break;
			case kNkWBFluorescentType_WarmWhite:
				printf("%u - WarmWhite\n", i);
				break;
			case kNkWBFluorescentType_White:
				printf("%u - White\n", i);
				break;
			case kNkWBFluorescentType_CoolWhite:
				printf("%u - CoolWhite\n", i);
				break;
			case kNkWBFluorescentType_DayWhite:
				printf("%u - DayWhite\n", i);
				break;
			case kNkWBFluorescentType_Daylight:
				printf("%u - Daylight\n", i);
				break;
			case kNkWBFluorescentType_HiTempMercuryVapor:
				printf("%u - HiTempMercuryVapor\n", i);
				break;

			}
		}
	}
	break;
	case kNkMAIDCapability_ExposureMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDExposureMode_Program:
				printf("%u - Program\n", i);
				break;
			case kNkMAIDExposureMode_AperturePriority:
				printf("%u - AperturePriority\n", i);
				break;
			case kNkMAIDExposureMode_SpeedPriority:
				printf("%u - SpeedPriority\n", i);
				break;
			case kNkMAIDExposureMode_Manual:
				printf("%u - Manual\n", i);
				break;
			case kNkMAIDExposureMode_Disable:
				printf("%u - Disable\n", i);
				break;
			case kNkMAIDExposureMode_Auto:
				printf("%u - Auto\n", i);
				break;
			case kNkMAIDExposureMode_Portrait:
				printf("%u - Portrait\n", i);
				break;
			case kNkMAIDExposureMode_Landscape:
				printf("%u - Landscape\n", i);
				break;
			case kNkMAIDExposureMode_Closeup:
				printf("%u - Closeup\n", i);
				break;
			case kNkMAIDExposureMode_Sports:
				printf("%u - Sports\n", i);
				break;
			case kNkMAIDExposureMode_NightPortrait:
				printf("%u - NightPortrait\n", i);
				break;
			case kNkMAIDExposureMode_NightView:
				printf("%u - NightView\n", i);
				break;
			case kNkMAIDExposureMode_Child:
				printf("%u - Child\n", i);
				break;
			case kNkMAIDExposureMode_FlashOff:
				printf("%u - FlashOff\n", i);
				break;
			case kNkMAIDExposureMode_Scene:
				printf("%u - Scene\n", i);
				break;
			case kNkMAIDExposureMode_Effects:
				printf("%u - Effects\n", i);
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieFocusMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieFocusMode_AFs:
				printf("%u - MovieFocusMode_AFs\n", i);
				break;

			case kNkMAIDMovieFocusMode_AFc:
				printf("%u - AFModeAtLiveView_C\n", i);
				break;

			case kNkMAIDMovieFocusMode_AFf:
				printf("%u - MovieFocusMode_AFf\n", i);
				break;

			case kNkMAIDMovieFocusMode_MF_FIX:
				printf("%u - MovieFocusMode_MF_FIX\n", i);
				break;

			case kNkMAIDMovieFocusMode_MF_SEL:
				printf("%u - MovieFocusMode_MF_SEL\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_FlashMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDFlashMode_Off:
				printf("%u - FlashMode_Off\n", i);
				break;

			case kNkMAIDFlashMode_Auto:
				printf("%u - FlashMode_Auto\n", i);
				break;

			case kNkMAIDFlashMode_On:
				printf("%u - FlashMode_On\n", i);
				break;

			case kNkMAIDFlashMode_FillFlash:
				printf("%u - FillFlash\n", i);
				break;

			case kNkMAIDFlashMode_RearCurtainSync:
				printf("%u - RearCurtainSync\n", i);
				break;

			case kNkMAIDFlashMode_SlowSyncFillFlash:
				printf("%u - SlowSyncFillFlash\n", i);
				break;

			case kNkMAIDFlashMode_RedEyeReductionLighting:
				printf("%u - RedEyeReductionLighting\n", i);
				break;

			case kNkMAIDFlashMode_SlowSyncRedEye:
				printf("%u - SlowSyncRedEye\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_SBIntegrationFlashReady:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDSBIntegrationFlashReady_NotReady:
				printf("%u - SBIntegrationFlashReady_NotReady\n", i);
				break;

			case kNkMAIDSBIntegrationFlashReady_Ready:
				printf("%u - SBIntegrationFlashReady_Ready\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_FlashRangeDisplay:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDFlashRangeDisplay_m:
				printf("%u - meter(m)\n", i);
				break;

			case kNkMAIDFlashRangeDisplay_ft:
				printf("%u - feet(ft)\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_OpticalMultipleFlashChannel:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDOpticalMultipleFlashChannel_1ch:
				printf("%u - OpticalMultipleFlashChannel_1ch\n", i);
				break;

			case kNkMAIDOpticalMultipleFlashChannel_2ch:
				printf("%u - OpticalMultipleFlashChannel_2ch\n", i);
				break;

			case kNkMAIDOpticalMultipleFlashChannel_3ch:
				printf("%u - OpticalMultipleFlashChannel_3ch\n", i);
				break;

			case kNkMAIDOpticalMultipleFlashChannel_4ch:
				printf("%u - OpticalMultipleFlashChannel_4ch\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_ExternalNewTypeFlashMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eNkMAIDExternalNewTypeFlashMode_OFF:
				printf("%u - ExternalNewTypeFlashMode_OFF\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_CompTTL:
				printf("%u - ExternalNewTypeFlashMode_CompTTL\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_NoCompTTL:
				printf("%u - ExternalNewTypeFlashMode_NoCompTTL\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_AA:
				printf("%u - ExternalNewTypeFlashMode_AA\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_ExtAutoFlash:
				printf("%u - ExternalNewTypeFlashMode_ExtAutoFlash\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_ManualLengthPriority:
				printf("%u - ExternalNewTypeFlashMode_ManualLengthPriority\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_Manual:
				printf("%u - ExternalNewTypeFlashMode_Manual\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_Multi:
				printf("%u - ExternalNewTypeFlashMode_Multi\n", i);
				break;

			case eNkMAIDExternalNewTypeFlashMode_NotExist:
				printf("%u - ExternalNewTypeFlashMode_NotExist\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ExtendedShutterSpeedsManual:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case 0:
				printf("%u - ExtendedShutterSpeedsManual_Off\n", i);
				break;

			case 1:
				printf("%u - ExtendedShutterSpeedsManual_On\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_RecordTimeCodes:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDRecordTimeCodes_Off:
				printf("%u - RecordTimeCodes_Off\n", i);
				break;

			case kNkMAIDRecordTimeCodes_On:
				printf("%u - RecordTimeCodes_On\n", i);
				break;

			case kNkMAIDRecordTimeCodes_OnWithHDMIOutput:
				printf("%u - RecordTimeCodes_OnWithHDMIOutput\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieFileType:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieFileType_R3D_HE:
				printf("%u - MovieFileType_R3D_HE\n", i);
				break;

			case kNkMAIDMovieFileType_MOV:
				printf("%u -MovieFileType_MOV\n", i);
				break;

			case kNkMAIDMovieFileType_MP4:
				printf("%u - MovieFileType_MP4\n", i);
				break;

			case kNkMAIDMovieFileType_H264_8bit_MP4:
				printf("%u - MovieFileType_H264_8bit_MP4\n", i);
				break;

			case kNkMAIDMovieFileType_H265_8bit_MOV:
				printf("%u - MovieFileType_H265_8bit_MOV\n", i);
				break;

			case kNkMAIDMovieFileType_H265_10bit_MOV:
				printf("%u - MovieFileType_H265_10bit_MOV\n", i);
				break;

			case kNkMAIDMovieFileType_ProRes422HQ_10bit_MOV:
				printf("%u - MovieFileType_ProRes422HQ_10bit_MOV\n", i);
				break;

			case kNkMAIDMovieFileType_ProResRawHQ_12bit_MOV:
				printf("%u - MovieFileType_ProResRawHQ_12bit_MOV\n", i);
				break;

			case kNkMAIDMovieFileType_NRaw_12bit_NEV:
				printf("%u - MovieFileType_NRaw_12bit_NEV\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_LiveViewImageStatus:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDLiveViewImageStatus_CannotAcquire:
				printf("%u -CannotAcquire\n", i);
				break;

			case kNkMAIDLiveViewImageStatus_CanAcquire:
				printf("%u - CanAcquire\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_LiveViewImageSize:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDLiveViewImageSize_QVGA:
				printf("%u -ImageSize_QVGA\n", i);
				break;
			case kNkMAIDLiveViewImageSize_VGA:
				printf("%u - ImageSize_VGA\n", i);
				break;
			case kNkMAIDLiveViewImageSize_XGA:
				printf("%u - ImageSize_XGA\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_LiveViewSelector:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDLiveViewSelector_Photo:
				printf("%u -LiveViewSelector_Photo\n", i);
				break;

			case kNkMAIDLiveViewSelector_Movie:
				printf("%u - LiveViewSelector_Movie\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_LiveViewZoomArea:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDLiveViewZoomArea_0:
				printf("%u -LiveViewZoomArea_0\n", i);
				break;
			case kNkMAIDLiveViewZoomArea_180:
				printf("%u - LiveViewZoomArea_180\n", i);
				break;
			case kNkMAIDLiveViewZoomArea_360:
				printf("%u - LiveViewZoomArea_360\n", i);
				break;
			case kNkMAIDLiveViewZoomArea_512:
				printf("%u -LiveViewZoomArea_512\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_640:
				printf("%u - LiveViewZoomArea_640\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_720:
				printf("%u -LiveViewZoomArea_720\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_1024:
				printf("%u - LiveViewZoomArea_1024\n", i);
				break;
			case kNkMAIDLiveViewZoomArea_1280:
				printf("%u -LiveViewZoomArea_1280\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_1448:
				printf("%u - LiveViewZoomArea_1448\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_2048:
				printf("%u -LiveViewZoomArea_2048\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_2560:
				printf("%u - LiveViewZoomArea_2560\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_2896:
				printf("%u -LiveViewZoomArea_2896\n", i);
				break;

			case kNkMAIDLiveViewZoomArea_1440:
				printf("%u -LiveViewZoomArea_1440\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_ShootingMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}
		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case eNkMAIDShootingMode_S:
				printf("%u -Single\n", i);
				break;
			case eNkMAIDShootingMode_C:
				printf("%u -Continuous L\n", i);
				break;
			case eNkMAIDShootingMode_CH:
				printf("%u -Continuous H\n", i);
				break;
			case eNkMAIDShootingMode_SelfTimer:
				printf("%u -Self Timer\n", i);
				break;
			case eNkMAIDShootingMode_MirrorUp:
				printf("%u -MirrorUp\n", i);
				break;
			case eNkMAIDShootingMode_RemoteTimer_Instant:
				printf("%u -RemoteTimer_Instant\n", i);
				break;
			case eNkMAIDShootingMode_RemoteTimer_2sec:
				printf("%u -RemoteTimer_2sec\n", i);
				break;
			case eNkMAIDShootingMode_LiveView:
				printf("%u -LiveView\n", i);
				break;
			case eNkMAIDShootingMode_RemoteCtrl:
				printf("%u -RemoteCtrl\n", i);
				break;
			case eNkMAIDShootingMode_Quiet:
				printf("%u -Quiet\n", i);
				break;
			case eNkMAIDShootingMode_QuietC:
				printf("%u -QuietC\n", i);
				break;
			case eNkMAIDShootingMode_CHPriorityFrame:
				printf("%u -Continuous H(Extended)\n", i);
				break;
			case 241:
				printf("%u -eCustomShootingMode_C30\n", i);
				break;
			case 242:
				printf("%u -eCustomShootingMode_C120\n", i);
				break;
			case 243:
				printf("%u -eCustomShootingMode_C60\n", i);
				break;
			case 244:
				printf("%u -eCustomShootingMode_C15\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	case kNkMAIDCapability_FlashISOAutoHighLimit:
	case kNkMAIDCapability_MovieISOAutoHiLimit:
	case kNkMAIDCapability_ISOAutoHiLimit:
	case kNkMAIDCapability_ISOAutoShutterTime:
	case kNkMAIDCapability_AFcPriority:
	case kNkMAIDCapability_AFsPriority:
	case kNkMAIDCapability_AFAreaSelector:
	case kNkMAIDCapability_FlashSyncTime:
	case kNkMAIDCapability_FlashSlowLimit:
	case kNkMAIDCapability_MovieAperture:
	case kNkMAIDCapability_Aperture:
	case kNkMAIDCapability_ShutterSpeed:
	case kNkMAIDCapability_MovieShutterSpeed:
	case kNkMAIDCapability_EVInterval:
	case kNkMAIDCapability_MovieSensitivity:
	case kNkMAIDCapability_Sensitivity:
	case kNkMAIDCapability_MovieWBMode:
	case kNkMAIDCapability_WBMode:
	case kNkMAIDCapability_BracketingOrder:
	case kNkMAIDCapability_WBPresetName:
	case kNkMAIDCapability_MovieWBPresetName:
	case kNkMAIDCapability_ImageSize:
	case kNkMAIDCapability_RawImageSize:
	case kNkMAIDCapability_CWMeteringDiameter:
	case kNkMAIDCapability_Slot2JpegImageSize:
	case kNkMAIDCapability_BracketingVary:
	case kNkMAIDCapability_CompressionLevel:
	case kNkMAIDCapability_ISOControlSensitivity:
	{
		if (stEnum.ulType != kNkMAIDArrayType_PackedString)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		char* psStr;
		ULONG	ulCount = 0;
		for (ULONG i = 0; i < stEnum.ulElements; ) {
			psStr = (char*)((char*)stEnum.pData + i);
			printf("%2d. %s\n", ulCount++, psStr);
			i += (ULONG)(strlen(psStr) + 1);
		}
	}
	break;

	case kNkMAIDCapability_MovieVibrationReduction:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieVibrationReduction_Off:
				printf("%u - MovieVibrationReduction_Off\n", i);
				break;

			case kNkMAIDMovieVibrationReduction_Normal:
				printf("%u - MovieVibrationReduction_Normal\n", i);
				break;

			case kNkMAIDMovieVibrationReduction_Sport:
				printf("%u - MovieVibrationReduction_Sport\n", i);
				break;

			case kNkMAIDMovieVibrationReduction_SamePhoto:
				printf("%u - MovieVibrationReduction_SamePhoto\n", i);
				break;

			default:
				printf("Invalid value returned\n");
				return FALSE;
			}
		}
	}
	break;

	case kNkMAIDCapability_MovieAttenuator:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDMovieAttenuator_disable:
				printf("%u - MovieAttenuator_disable\n", i);
				break;

			case kNkMAIDMovieAttenuator_enable:
				printf("%u - MovieAttenuator_enable\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_AFAreaPoint:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNkMAIDAFAreaPoint_51:
				printf("%u - AFAreaPoint_51\n", i);
				break;
			case kNkMAIDAFAreaPoint_11:
				printf("%u - AFAreaPoint_11\n", i);
				break;
			case kNkMAIDAFAreaPoint_39:
				printf("%u - AFAreaPoint_39\n", i);
				break;
			case kNkMAIDAFAreaPoint_55:
				printf("%u - AFAreaPoint_55\n", i);
				break;
			case kNkMAIDAFAreaPoint_15:
				printf("%u - AFAreaPoint_15\n", i);
				break;
			case kNkMAIDAFAreaPoint_All:
				printf("%u - AFAreaPoint_All\n", i);
				break;
			case kNkMAIDAFAreaPoint_Skip:
				printf("%u - AFAreaPoint_Skip\n", i);
				break;
			case kNkMAIDAFAreaPoint_105:
				printf("%u - AFAreaPoint_105\n", i);
				break;
			case kNkMAIDAFAreaPoint_27:
				printf("%u - AFAreaPoint_27\n", i);
				break;
			default:
				printf("Value not supported by TestApp val = %d\n", ((ULONG*)(stEnum.pData))[i]);
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MovieSkinSoftening:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNKMAIDMovieSkinSoftening_Off:
				printf("%u - Off\n", i);
				break;

			case kNKMAIDMovieSkinSoftening_Low:
				printf("%u - Low\n", i);
				break;

			case kNKMAIDMovieSkinSoftening_Normal:
				printf("%u - Normal\n", i);
				break;

			case kNKMAIDMovieSkinSoftening_High:
				printf("%u - High\n", i);
				break;

			case kNKMAIDMovieSkinSoftening_SameAsStill:
				printf("%u - SameAsStill\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_SkinSoftening:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNKMAIDSkinSoftening_Off:
				printf("%u - Off\n", i);
				break;

			case kNKMAIDSkinSoftening_Low:
				printf("%u - Low\n", i);
				break;

			case kNKMAIDSkinSoftening_Normal:
				printf("%u - Normal\n", i);
				break;

			case kNKMAIDSkinSoftening_High:
				printf("%u - High\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_PortraitImpressionBalance:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNKMAIDPortraitImpressionBalance_Off:
				printf("%u - Off\n", i);
				break;

			case kNKMAIDPortraitImpressionBalance_Mode1:
				printf("%u - Mode1\n", i);
				break;

			case kNKMAIDPortraitImpressionBalance_Mode2:
				printf("%u - Mode2\n", i);
				break;

			case kNKMAIDPortraitImpressionBalance_Mode3:
				printf("%u - Mode3\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_SpecialShootingMode:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNKMAIDSpecialShootingMode_Off:
				printf("%u - Off\n", i);
				break;

			case kNKMAIDSpecialShootingMode_Interval:
				printf("%u - Interval\n", i);
				break;

			case kNKMAIDSpecialShootingMode_FocusShift:
				printf("%u - FocusShift\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;
	case kNkMAIDCapability_MoviePortraitImpressionBalance:
	{
		if (stEnum.ulType != kNkMAIDArrayType_Unsigned)
		{
			printf("Invalid array type returned\n");
			return false;
		}

		for (ULONG i = 0; i < stEnum.ulElements; i++)
		{
			switch (((ULONG*)(stEnum.pData))[i])
			{
			case kNKMAIDMoviePortraitImpressionBalance_Off:
				printf("%u - Off\n", i);
				break;

			case kNKMAIDMoviePortraitImpressionBalance_Mode1:
				printf("%u - Mode1\n", i);
				break;

			case kNKMAIDMoviePortraitImpressionBalance_Mode2:
				printf("%u - Mode2\n", i);
				break;

			case kNKMAIDMoviePortraitImpressionBalance_Mode3:
				printf("%u - Mode3\n", i);
				break;

			default:
				printf("Value not supported by TestApp val = %d\n", (((ULONG*)(stEnum.pData))[i]));
				break;
			}
		}
	}
	break;

	default:
		break;
	}
	return true;
}

BOOL SetFloatCapability(ULONG ulCapID, LPVOID pCapValue, eNkMAIDDataType eDataType)
{
	float new_val;
	char	buf[256];

	bool set_cap_applicable = false;

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);

	if (!set_cap_applicable)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_FloatPtr)
		{
			printf("Invalid data type returned\n");
			return false;
		}
		else
		{
			printf("Cap Value = %f\n", *((float*)pCapValue));
		}

		freeByDataType(pCapValue, eDataType);
	}

	set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	printf("Input new value\n>");
	scanf("%s", buf);
	new_val = (float)atof(buf);
	lerror = g_pMAIDSetCapability(ulCapID, &new_val, kNkMAIDDataType_FloatPtr);

	return true;
}

void freeByDataType(void* data, eNkMAIDDataType type)
{
	void* client_data;

	switch (type)
	{
	case kNkMAIDDataType_EnumPtr:
	{
		client_data = ((LPNkMAIDEnum)data)->pData;
		free(client_data);
		free(data);
		break;
	}

	case kNkMAIDDataType_ArrayPtr:
	{
		client_data = ((LPNkMAIDArray)data)->pData;
		free(client_data);
		free(data);
		break;
	}

	case kNkMAIDDataType_BooleanPtr:
	case kNkMAIDDataType_IntegerPtr:
	case kNkMAIDDataType_UnsignedPtr:
	case kNkMAIDDataType_FloatPtr:
	case kNkMAIDDataType_PointPtr:
	case kNkMAIDDataType_SizePtr:
	case kNkMAIDDataType_RectPtr:
	case kNkMAIDDataType_StringPtr:
	case kNkMAIDDataType_DateTimePtr:
	case kNkMAIDDataType_RangePtr:
	case kNkMAIDDataType_ObjectPtr:
	case kNkMAIDDataType_CapInfoPtr:
	case kNkMAIDDataType_GenericPtr:
	{
		free(data);
	}
	break;

	default:
		printf("ERROR: Invalid pointer passed");
	}
}


/********Shows the current setting of a Range type capability and set a value for it.*****************/

BOOL SetRangeCapability(ULONG ulCapID)
{
	NkMAIDRange* stRange;
	LPVOID pCapValue;
	eNkMAIDDataType eDataType = kNkMAIDDataType_Null;
	double lfValue;
	char buf[256];

	bool isCapResent = CheckCapability(ulCapID, kNkMAIDCapOperation_Get);
	if (isCapResent == false)
		return false;

	NKERROR lerror = g_pMAIDGetCapability(ulCapID, kNkSDKGetSettingValue, pCapValue, eDataType);
	stRange = (NkMAIDRange*)pCapValue;
	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		if (pCapValue) freeByDataType(pCapValue, eDataType);
		printf("Failed to get capability value\n");
		return false;
	}
	else if (eDataType != kNkMAIDDataType_RangePtr)
	{
		printf("Invalid data type returned\n");
		return false;
	}

	if (stRange->ulSteps == 0) {
		// the value of this capability is set to 'lfValue' directly
		printf("Current Value: %f  (Max: %f  Min: %f)\n", stRange->lfValue, stRange->lfUpper, stRange->lfLower);
	}
	else {
		// the value of this capability is calculated from 'ulValueIndex'
		for (ULONG i = 0; i < stRange->ulSteps; i++)
		{
			double value = stRange->lfLower + i * (stRange->lfUpper - stRange->lfLower) / (stRange->ulSteps - 1);
			printf("%d - %lf \n", i, value);
		}
		lfValue = stRange->lfLower + stRange->ulValueIndex * (stRange->lfUpper - stRange->lfLower) / (stRange->ulSteps - 1);
		printf("Current Value: %f  (Max: %f  Min: %f  Step: %u   ValueIndex: %u)\n", lfValue, stRange->lfUpper, stRange->lfLower, stRange->ulSteps, stRange->ulValueIndex);
	}
	BOOL set_cap_applicable = CheckCapability(ulCapID, kNkMAIDCapOperation_Set);

	if (!set_cap_applicable)
		return false;

	printf("Input new value.\n>");
	scanf("%s", buf);

	if (stRange->ulSteps == 0) {
		stRange->lfValue = atof(buf);
	}
	else {
		lfValue = atof(buf);
		stRange->ulValueIndex = (ULONG)((lfValue - stRange->lfLower) * (stRange->ulSteps - 1) / (stRange->lfUpper - stRange->lfLower));
	}
	lerror = g_pMAIDSetCapability(ulCapID, stRange, kNkMAIDDataType_RangePtr);
	PERROR(lerror);
	freeByDataType(pCapValue, eDataType);
	return TRUE;
}

void PERROR(NKERROR lerror)
{
	if (lerror != 0)
	{
		printf("Value not changed");
	}
}

BOOL GetSBAttrDesc()
{
	BOOL					bRet = TRUE;
	char					buf[256] = { 0 };
	ULONG					ulSBHandleMenu = 0;
	ULONG					ulSBHandle = 0;
	ULONG					ulSBAttrID = 0;
	FILE* fileStream;
	NkMAIDGetSBAttrDesc		stSbAttrDesc;
	LPNkMAIDCapInfo			pCapInfo = NULL;
	SLONG nResult = kNkMAIDResult_NoError;

	// To clear the structure.
	memset(&stSbAttrDesc, 0, sizeof(NkMAIDGetSBAttrDesc));

	// To display the menu.
	printf("\nSelect SBHandle Menu(0-1, 2)\n");
	printf(" 0. All\n");
	printf(" 1. Any value\n");
	printf(" 2. Exit\n>");
	scanf("%s", buf);
	ulSBHandleMenu = (ULONG)atoi(buf);

	// Check the input value.
	if (ulSBHandleMenu >= 2)
	{
		return TRUE;
	}
	else if (ulSBHandleMenu == 1)
	{
		// To display the menu.
		printf("\nEnter SBHandle Value(Hex)\n");
		printf("0x");
		scanf("%s", buf);

		char* pcErrbuf;
		ulSBHandle = (ULONG)strtol(buf, &pcErrbuf, 16);
		if (*pcErrbuf != '\0')
		{
			return TRUE;
		}
	}
	else
	{
		ulSBHandle = kNkMAIDSBHandle_ALL;
	}

	// To display the menu.
	printf("\nSelect SB Attribute(1-5, 0)\n");
	printf(" 1. SB Attribute All\n");
	printf(" 2. SB Attribute Name\n");
	printf(" 3. SB Attribute GroupID\n");
	printf(" 4. SB Attribute Status\n");
	printf(" 5. SB Attribute TestFlashDisable\n");
	printf(" 0. Exit\n>");
	scanf("%s", buf);
	ulSBAttrID = (ULONG)atoi(buf);

	// Check the input value.
	if ((ulSBAttrID == 0) || (ulSBAttrID > 5))
	{
		return TRUE;
	}

	if (CheckCapability(kNkMAIDCapability_GetSBAttrDesc, kNkMAIDCapOperation_Get) == FALSE)
	{
		return FALSE;
	}

	ULONG ulCapType;
	GetCapabilityType(kNkMAIDCapability_GetSBAttrDesc, ulCapType);

	// check data type of the capability
	if (ulCapType != kNkMAIDCapType_Generic)
	{
		return FALSE;
	}

	// 1.To get the size of the order of the SB attribute descriptor acquisition.
	{
		// ulSBHandle:To specify the SBHandle to be acquisition target.
		stSbAttrDesc.ulSBHandle = ulSBHandle;

		// ulSBAttrID:To specify the SBAttrID to be acquisition target.
		switch (ulSBAttrID)
		{
		case 1:
			// SBAttribute_ALL
			stSbAttrDesc.ulSBAttrID = kNkMAIDSBAttribute_ALL;
			break;
		case 2:
			// SBAttribute_Name
			stSbAttrDesc.ulSBAttrID = kNkMAIDSBAttribute_Name;
			break;
		case 3:
			// SBAttribute_GroupID
			stSbAttrDesc.ulSBAttrID = kNkMAIDSBAttribute_GroupID;
			break;
		case 4:
			// SBAttribute_Status
			stSbAttrDesc.ulSBAttrID = kNkMAIDSBAttribute_Status;
			break;
		case 5:
			// SBAttribute_TestFlashDisable
			stSbAttrDesc.ulSBAttrID = kNkMAIDSBAttribute_TestFlashDisable;
			break;
		default:
			stSbAttrDesc.ulSBAttrID = 0;
			break;
		}

		// ulSize:0 is specified.
		stSbAttrDesc.ulSize = 0;

		eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;
		LPVOID pCapValue = &stSbAttrDesc;

		// To get the size of the order of the SB attribute descriptor acquisition.
		NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_GetSBAttrDesc, kNkSDKGetSettingValue, pCapValue, eDataType);

		if (lerror == kNkMAIDResult_UnexpectedError)
		{
			printf("\nNot supported SBAttrDesc.\n");
			return TRUE;
		}
		else if (lerror != kNkMAIDResult_NoError)
		{
			// abnomal.
			printf("\nFailed in getting SBAttrDesc.\n");

			return FALSE;
		}
	}

	// Save to file
	// open file
	fileStream = fopen("SBAttrDesc.dat", "wb");
	if (fileStream == NULL)
	{
		// abnomal.
		printf("\nFile open error.\n");
		free(stSbAttrDesc.pData);

		return FALSE;
	}

	// Get data pointer
	unsigned char* pucData = NULL;
	pucData = (unsigned char*)stSbAttrDesc.pData;

	// write file
	fwrite(pucData, 1, stSbAttrDesc.ulSize, fileStream);
	printf("\nSBAttrDesc.dat was saved.\n");

	// close file
	fclose(fileStream);
	free(stSbAttrDesc.pData);

	return TRUE;
}

BOOL GetSBAttrValue()
{
	NkMAIDSBAttrValue	stSbAttrValue;
	BOOL				bRet = TRUE;
	char				buf[256] = { 0 };
	ULONG				ulSBHandleMenu = 0;
	ULONG				ulSBHandle = 0;
	ULONG				ulSBAttrID = 0;
	FILE* fileStream;
	LPNkMAIDCapInfo		pCapInfo = NULL;
	SLONG nResult = kNkMAIDResult_NoError;

	memset(&stSbAttrValue, 0, sizeof(NkMAIDSBAttrValue));

	// To display the menu.
	printf("\nSelect SBHandle Menu(0-1, 2)\n");
	printf(" 0. All\n");
	printf(" 1. Any value\n");
	printf(" 2. Exit\n>");
	scanf("%s", buf);
	ulSBHandleMenu = (ULONG)atoi(buf);

	// Check the input value.
	if (ulSBHandleMenu >= 2)
	{
		return TRUE;
	}
	else if (ulSBHandleMenu == 1)
	{
		// To display the menu.
		printf("\nEnter SBHandle Value(Hex)\n");
		printf("0x");
		scanf("%s", buf);

		char* pcErrbuf;
		ulSBHandle = (ULONG)strtol(buf, &pcErrbuf, 16);
		if (*pcErrbuf != '\0')
		{
			return TRUE;
		}
	}
	else
	{
		ulSBHandle = kNkMAIDSBHandle_ALL;
	}

	// To display the menu.
	printf("\nSelect SBAttribute(1-5, 0)\n");
	printf(" 1. SBAttribute ALL\n");
	printf(" 2. SBAttribute Name\n");
	printf(" 3. SBAttribute GroupID\n");
	printf(" 4. SBAttribute Status\n");
	printf(" 5. SBAttribute TestFlashDisable\n");
	printf(" 0. Exit\n>");
	scanf("%s", buf);
	ulSBAttrID = (ULONG)atoi(buf);

	// Check the input value.
	if ((ulSBAttrID == 0) || (ulSBAttrID > 5))
	{
		return TRUE;
	}

	if (CheckCapability(kNkMAIDCapability_SBAttrValue, kNkMAIDCapOperation_Get) == FALSE)
	{
		return FALSE;
	}

	ULONG ulCapType;
	GetCapabilityType(kNkMAIDCapability_SBAttrValue, ulCapType);

	// check data type of the capability
	if (ulCapType != kNkMAIDCapType_Generic)
	{
		return FALSE;
	}

	{
		// ulSBHandle:To specify the SBHandle to be acquisition target.
		stSbAttrValue.ulSBHandle = ulSBHandle;

		// ulSBAttrID:To specify the SBAttrID to be acquisition target.
		switch (ulSBAttrID)
		{
		case 1:
			// SBAttribute_ALL
			stSbAttrValue.ulSBAttrID = kNkMAIDSBAttribute_ALL;
			break;
		case 2:
			// SBAttribute_Name
			stSbAttrValue.ulSBAttrID = kNkMAIDSBAttribute_Name;
			break;
		case 3:
			// SBAttribute_GroupID
			stSbAttrValue.ulSBAttrID = kNkMAIDSBAttribute_GroupID;
			break;
		case 4:
			// SBAttribute_Status
			stSbAttrValue.ulSBAttrID = kNkMAIDSBAttribute_Status;
			break;
		case 5:
			// SBAttribute_TestFlashDisable
			stSbAttrValue.ulSBAttrID = kNkMAIDSBAttribute_TestFlashDisable;
			break;
		default:
			stSbAttrValue.ulSBAttrID = 0;
			break;
		}

		// ulSize:0 is specified.
		stSbAttrValue.ulSize = 0;

		eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;
		LPVOID pCapValue = &stSbAttrValue;

		// To get the size of the order of the SB attribute descriptor acquisition.
		NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_SBAttrValue, kNkSDKGetSettingValue, pCapValue, eDataType);

		if (lerror == kNkMAIDResult_UnexpectedError)
		{
			printf("\nNot supported SBAttrValue.\n");
			return TRUE;
		}
		else if (lerror != kNkMAIDResult_NoError)
		{
			// abnomal.
			printf("\nFailed in getting SBAttrValue.\n");

			return FALSE;
		}
	}

	// Save to file
	// open file
	fileStream = fopen("SBAttrValue.dat", "wb");
	if (fileStream == NULL)
	{
		// abnomal.
		printf("\nFile open error.\n");
		free(stSbAttrValue.pData);

		return FALSE;
	}

	// Get data pointer
	unsigned char* pucData = NULL;
	pucData = (unsigned char*)stSbAttrValue.pData;

	// write file
	fwrite(pucData, 1, stSbAttrValue.ulSize, fileStream);
	printf("\nSBAttrValue.dat was saved.\n");

	// close file
	fclose(fileStream);
	free(stSbAttrValue.pData);

	return TRUE;
}

BOOL GetSBGroupAttrDesc()
{

	BOOL						bRet = TRUE;
	char						buf[256] = { 0 };
	ULONG						ulSBGroupID;
	ULONG						ulSBGroupAttrID;
	FILE* fileStream;
	NkMAIDGetSBGroupAttrDesc	stSbGroupAttrDesc;
	LPNkMAIDCapInfo				pCapInfo = NULL;

	// To clear the structure.
	memset(&stSbGroupAttrDesc, 0, sizeof(NkMAIDGetSBGroupAttrDesc));

	// To display the menu.
	printf("\nSelect SBGroupID(1-8, 0)\n");
	printf(" 1. All\n");
	printf(" 2. Master\n");
	printf(" 3. A\n");
	printf(" 4. B\n");
	printf(" 5. C\n");
	printf(" 6. D\n");
	printf(" 7. E\n");
	printf(" 8. F\n");
	printf(" 0. Exit\n>");
	scanf("%s", buf);
	ulSBGroupID = (ULONG)atoi(buf);

	// Check the input value.
	if ((ulSBGroupID == 0) || (ulSBGroupID > 8))
	{
		return TRUE;
	}

	// To display the menu.
	printf("\nSelect SBGroupAttrID(1-10, 0)\n");
	printf(" 1. All\n");
	printf(" 2. FlashMode\n");
	printf(" 3. FlashCompensation\n");
	printf(" 4. FlashRatio\n");
	printf(" 5. FlashLevel\n");
	printf(" 6. FlashRange\n");
	printf(" 7. Repeat\n");
	printf(" 8. RepeatCount\n");
	printf(" 9. RepeatInterval\n");
	printf("10. Invalid\n");
	printf(" 0. Exit\n>");
	scanf("%s", buf);
	ulSBGroupAttrID = (ULONG)atoi(buf);

	// Check the input value.
	if ((ulSBGroupAttrID == 0) || (ulSBGroupAttrID > 10))
	{
		return TRUE;
	}

	if (CheckCapability(kNkMAIDCapability_GetSBGroupAttrDesc, kNkMAIDCapOperation_Get) == FALSE)
	{
		return FALSE;
	}

	ULONG ulCapType;
	GetCapabilityType(kNkMAIDCapability_GetSBGroupAttrDesc, ulCapType);

	// check data type of the capability
	if (ulCapType != kNkMAIDCapType_Generic)
	{
		return FALSE;
	}

	// 1.To get the size of the order of the SB group attribute descriptor acquisition.
	{
		// ulSBGroupID:To specify the SBGroupID to be acquisition target.
		switch (ulSBGroupID)
		{
		case 1:
			// SBGroupID_All
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_ALL;
			break;
		case 2:
			// SBGroupID_Master
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_Master;
			break;
		case 3:
			// SBGroupID_A
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_A;
			break;
		case 4:
			// SBGroupID_B
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_B;
			break;
		case 5:
			// SBGroupID_C
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_C;
			break;
		case 6:
			// SBGroupID_D
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_D;
			break;
		case 7:
			// SBGroupID_E
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_E;
			break;
		case 8:
			// SBGroupID_F
			stSbGroupAttrDesc.ulSBGroupID = kNkMAIDSBGroupID_F;
			break;
		default:
			break;
		}

		// ulSBGroupAttrID:To specify the SBGroupAttrID to be acquisition target.
		switch (ulSBGroupAttrID)
		{
		case 1:
			// SBGroupAttribute_All
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_ALL;
			break;
		case 2:
			// SBGroupAttribute_FlashMode
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashMode;
			break;
		case 3:
			// SBGroupAttribute_FlashCompensation
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashCompensation;
			break;
		case 4:
			// SBGroupAttribute_FlashRatio
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashRatio;
			break;
		case 5:
			// SBGroupAttribute_FlashLevel
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashLevel;
			break;
		case 6:
			// SBGroupAttribute_FlashRange
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashRange;
			break;
		case 7:
			// SBGroupAttribute_Repeat
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_Repeat;
			break;
		case 8:
			// SBGroupAttribute_RepeatCount
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_RepeatCount;
			break;
		case 9:
			// SBGroupAttribute_RepeatInterval
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_RepeatInterval;
			break;
		case 10:
			// SBGroupAttribute_Invalid
			stSbGroupAttrDesc.ulSBGroupAttrID = kNkMAIDSBGroupAttribute_Invalid;
			break;
		default:
			break;
		}

		// ulSize:0 is specified.
		stSbGroupAttrDesc.ulSize = 0;

		eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;
		LPVOID pCapValue = &stSbGroupAttrDesc;

		// To get the size of the order of the SB attribute descriptor acquisition.
		NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_GetSBGroupAttrDesc, kNkSDKGetSettingValue, pCapValue, eDataType);

		if (lerror == kNkMAIDResult_UnexpectedError)
		{
			printf("\nNot supported SBGroupAttrDesc.\n");
			return TRUE;
		}
		else if (lerror != kNkMAIDResult_NoError)
		{
			// abnomal.
			printf("\nFailed in getting SBGroupAttrDesc.\n");

			return FALSE;
		}
	}

	// Save to file
	// open file
	fileStream = fopen("SBGroupAttrDesc.dat", "wb");
	if (fileStream == NULL)
	{
		// abnomal.
		printf("\nfile open error.\n");
		free(stSbGroupAttrDesc.pData);

		return FALSE;
	}

	// Get data pointer
	unsigned char* pucData = NULL;
	pucData = (unsigned char*)stSbGroupAttrDesc.pData;

	// write file
	fwrite(pucData, 1, stSbGroupAttrDesc.ulSize, fileStream);
	printf("\nSBGroupAttrDesc.dat was saved.\n");

	// close file
	fclose(fileStream);
	free(stSbGroupAttrDesc.pData);

	return TRUE;
}

BOOL GetSBGroupAttrValue()
{
	BOOL				bRet = TRUE;
	char				buf[256] = { 0 };
	ULONG				ulSBGroupID;
	ULONG				ulSBGroupAttrID;
	FILE* fileStream;
	LPNkMAIDCapInfo		pCapInfo = NULL;
	NkMAIDSBGroupAttrValue stSbGroupAttrValue, * pstSbGroupAttrValue;
	memset(&stSbGroupAttrValue, 0, sizeof(NkMAIDSBGroupAttrValue));
	pstSbGroupAttrValue = &stSbGroupAttrValue;

	// To display the menu.
	printf("\nSelect SBGroupID(1-8, 0)\n");
	printf(" 1. SBGroupID ALL\n");
	printf(" 2. SBGroupID Master\n");
	printf(" 3. SBGroupID A\n");
	printf(" 4. SBGroupID B\n");
	printf(" 5. SBGroupID C\n");
	printf(" 6. SBGroupID D\n");
	printf(" 7. SBGroupID E\n");
	printf(" 8. SBGroupID F\n");
	printf(" 0. Exit\n>");
	scanf("%s", buf);
	ulSBGroupID = (ULONG)atoi(buf);

	// Check the input value.
	if ((ulSBGroupID == 0) || (ulSBGroupID > 8))
	{
		return TRUE;
	}

	// To display the menu.
	printf("\nSelect SBGroupAttrID(1-10, 0)\n");
	printf(" 1. All\n");
	printf(" 2. FlashMode\n");
	printf(" 3. FlashCompensation\n");
	printf(" 4. FlashRatio\n");
	printf(" 5. FlashLevel\n");
	printf(" 6. FlashRange\n");
	printf(" 7. Repeat\n");
	printf(" 8. RepeatCount\n");
	printf(" 9. RepeatInterval\n");
	printf("10. Invalid\n");
	printf(" 0. Exit\n>");
	scanf("%s", buf);
	ulSBGroupAttrID = (ULONG)atoi(buf);

	// Check the input value.
	if ((ulSBGroupAttrID == 0) || (ulSBGroupAttrID > 10))
	{
		return TRUE;
	}

	if (CheckCapability(kNkMAIDCapability_SBGroupAttrValue, kNkMAIDCapOperation_Get) == FALSE)
	{
		return FALSE;
	}

	ULONG ulCapType;
	GetCapabilityType(kNkMAIDCapability_SBGroupAttrValue, ulCapType);

	// check data type of the capability
	if (ulCapType != kNkMAIDCapType_Generic)
	{
		return FALSE;
	}

	// 1.To get the size in order to obtain the current value of SB group attributes.
	{
		// ulSBGroupID:To specify the SBGroupID to be acquisition target.
		switch (ulSBGroupID)
		{
		case 1:
			// SBGroupID_All
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_ALL;
			break;
		case 2:
			// SBGroupID_Master
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_Master;
			break;
		case 3:
			// SBGroupID_A
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_A;
			break;
		case 4:
			// SBGroupID_B
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_B;
			break;
		case 5:
			// SBGroupID_C
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_C;
			break;
		case 6:
			// SBGroupID_D
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_D;
			break;
		case 7:
			// SBGroupID_E
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_E;
			break;
		case 8:
			// SBGroupID_F
			pstSbGroupAttrValue->ulSBGroupID = kNkMAIDSBGroupID_F;
			break;
		default:
			break;
		}

		// ulSBGroupAttrID:To specify the SBGroupAttrID to be acquisition target.
		switch (ulSBGroupAttrID)
		{
		case 0:
			break;
		case 1:
			// SBGroupAttribute_All
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_ALL;
			break;
		case 2:
			// SBGroupAttribute_FlashMode
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashMode;
			break;
		case 3:
			// SBGroupAttribute_FlashCompensation
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashCompensation;
			break;
		case 4:
			// SBGroupAttribute_FlashRatio
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashRatio;
			break;
		case 5:
			// SBGroupAttribute_FlashLevel
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashLevel;
			break;
		case 6:
			// SBGroupAttribute_FlashRange
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_FlashRange;
			break;
		case 7:
			// SBGroupAttribute_Repeat
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_Repeat;
			break;
		case 8:
			// SBGroupAttribute_RepeatCount
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_RepeatCount;
			break;
		case 9:
			// SBGroupAttribute_RepeatInterval
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_RepeatInterval;
			break;
		case 10:
			// SBGroupAttribute_Invalid
			pstSbGroupAttrValue->ulSBGroupAttrID = kNkMAIDSBGroupAttribute_Invalid;
			break;
		default:
			break;
		}

		// ulSize:0 is specified.
		pstSbGroupAttrValue->ulSize = 0;

		eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;
		LPVOID pCapValue = pstSbGroupAttrValue;

		// To get the size of the order of the SB attribute descriptor acquisition.
		NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_SBGroupAttrValue, kNkSDKGetSettingValue, pCapValue, eDataType);

		if (lerror == kNkMAIDResult_UnexpectedError)
		{
			printf("\nNot supported SBGroupAttrValue.\n");
			return TRUE;
		}
		else if (lerror != kNkMAIDResult_NoError)
		{
			// abnomal.
			printf("\nFailed in getting SBGroupAttrValue.\n");

			return FALSE;
		}
	}

	// Save to file
	// open file
	fileStream = fopen("SBGroupAttrValue.dat", "wb");
	if (fileStream == NULL)
	{
		// abnomal.
		printf("\nFile open error.\n");
		free(pstSbGroupAttrValue->pData);

		return FALSE;
	}

	// Get data pointer
	unsigned char* pucData = NULL;
	pucData = (unsigned char*)pstSbGroupAttrValue->pData;

	// write file
	fwrite(pucData, 1, pstSbGroupAttrValue->ulSize, fileStream);
	printf("\nSBGroupAttrValue.dat was saved.\n");

	// close file
	fclose(fileStream);
	free(pstSbGroupAttrValue->pData);

	return TRUE;
}

BOOL StartTestFlash()
{
	NKERROR lerror = g_pMAIDStartOperation(kNkMAIDCapability_TestFlash, NULL, NULL);
	if (lerror != kNkMAIDResult_NoError)
		printf("Unable test flash.");
	return TRUE;
}

BOOL CheckCapabilityupdated(ULONG ulCapID, eNkMAIDCapOperations operationDesc)
{
	ULONG j = 0;
	LPNkMAIDEnumCapInfo pEnumCapInfoupdate = NULL;
	NKERROR err = g_pMAIDEnumCapabilities(pEnumCapInfoupdate, NULL, NULL);

	if (err != kNkMAIDResult_NoError)
	{
		printf("Unable to get the updated capability list\n");
		return FALSE;
	}

	for (j = 0; j < pEnumCapInfoupdate->ulCapCount; j++)
	{
		if (pEnumCapInfoupdate->pCapArray[j].ulID == ulCapID)
			break;
	}

	if (j == pEnumCapInfoupdate->ulCapCount)
	{
		printf("capability not found\n");
		return FALSE;
	}

	if (!(pEnumCapInfoupdate->pCapArray[j].ulOperations & operationDesc))
	{
		switch (operationDesc)
		{
		case kNkMAIDCapOperation_Get:
			printf("Capability Get operation not allowed");
			break;

		case kNkMAIDCapOperation_Set:
			printf("Capability Set operation not allowed");
			break;

		case kNkMAIDCapOperation_GetArray:
			printf("Capability GetArray operation not allowed");
			break;

		default:
			printf("Capability GetDefault operation not allowed");
			break;
		}

		return FALSE;
	}

	return TRUE;
}

BOOL IsCapabilityAvailable(ULONG ulCapID)
{
	ULONG j = 0;

	m_capability_list_lock.lock();

	for (j = 0; j < pEnumCapInfo->ulCapCount; j++)
	{
		if (pEnumCapInfo->pCapArray[j].ulID == ulCapID)
			break;
	}

	if (j == pEnumCapInfo->ulCapCount)
	{
		m_capability_list_lock.unlock();
		return FALSE;
	}

	m_capability_list_lock.unlock();

	return TRUE;
}

BOOL GetSetPortraitImpressionBalanceDataSet()
{
	bool set_cap_applicable = false;
	NKMAIDPortraitImpressionBalanceDataSet stPIBDataSet;
	memset(&stPIBDataSet, 0, sizeof(NKMAIDPortraitImpressionBalanceDataSet));

	stPIBDataSet.ulDefaultFlag = 0;
	stPIBDataSet.ulLiveViewMode = 0;
	stPIBDataSet.ulMode = kNKMAIDMoviePortraitImpressionBalance_Mode1;

	LPVOID pCapValue = &stPIBDataSet;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_PortraitImpressionBalanceDataSet, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_PortraitImpressionBalanceDataSet, ulDataType) == false)
		return FALSE;
	if (ulDataType != kNkMAIDCapType_Generic) return FALSE;

	NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_PortraitImpressionBalanceDataSet, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		printf("Failed to get capability value\n");
		return FALSE;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_GenericPtr)
		{
			printf("Invalid data type returned\n");
			return FALSE;
		}
		else
		{
			if (stPIBDataSet.ulNumElement == 0)
				printf("Data is empty\n");
			for (ULONG i = 0; i < stPIBDataSet.ulNumElement; i++)
			{
				printf("ulMode = %d, lHue = %d, lBrightness = %d\n", stPIBDataSet.stElementInfo[i].ulMode, stPIBDataSet.stElementInfo[i].lHue, stPIBDataSet.stElementInfo[i].lBrightness);
			}

		}
	}

	if (CheckCapability(kNkMAIDCapability_PortraitImpressionBalanceDataSet, kNkMAIDCapOperation_Set) == false)
		return FALSE;

	stPIBDataSet.ulMode = kNKMAIDMoviePortraitImpressionBalance_Mode1;
	stPIBDataSet.ulLiveViewMode = 0;
	printf("Enter Mode\t");
	scanf("%d", &stPIBDataSet.ulMode);
	printf("Enter Brightness\t");
	scanf("%d", &stPIBDataSet.lBrightness);
	printf("Enter Hue\t");
	scanf("%d", &stPIBDataSet.lHue);
	printf("\n");

	lerror = g_pMAIDSetCapability(kNkMAIDCapability_PortraitImpressionBalanceDataSet, &stPIBDataSet, kNkMAIDDataType_GenericPtr);
	PERROR(lerror);

	return TRUE;
}

BOOL GetSetPowerZoomDrive()
{
	bool set_cap_applicable = false;
	NkMAIDPowerZoomDrive stPowerZoomDrive;
	memset(&stPowerZoomDrive, 0, sizeof(NkMAIDPowerZoomDrive));

	stPowerZoomDrive.ulPowerZoomDrive = 1;
	stPowerZoomDrive.ulDriveDirection = 1;
	stPowerZoomDrive.ulDriveSpeed = 5;

	LPVOID pCapValue = &stPowerZoomDrive;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_PowerZoomDrive, kNkMAIDCapOperation_Get) != false)
	{
		// check data type of the capability
		ULONG ulDataType;
		if (GetCapabilityType(kNkMAIDCapability_PowerZoomDrive, ulDataType) == false)
			return FALSE;

		if (ulDataType != kNkMAIDCapType_Generic) return FALSE;

		NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_PowerZoomDrive, kNkSDKGetSettingValue, pCapValue, eDataType);

		if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
		{
			printf("Failed to get capability value\n");
			return FALSE;
		}
		else
		{
			if (eDataType != kNkMAIDDataType_GenericPtr)
			{
				printf("Invalid data type returned\n");
				return FALSE;
			}
			else
			{
				printf("stPowerZoomDrive.ulPowerZoomDrive = %d, ulDriveDirection = %d, ulDriveSpeed = %d\n",
					stPowerZoomDrive.ulPowerZoomDrive, stPowerZoomDrive.ulDriveDirection, stPowerZoomDrive.ulDriveSpeed);
			}
		}
	}

	if (CheckCapability(kNkMAIDCapability_PowerZoomDrive, kNkMAIDCapOperation_Set) == false)
		return FALSE;

	stPowerZoomDrive.ulPowerZoomDrive = 1;
	stPowerZoomDrive.ulDriveDirection = 1;
	stPowerZoomDrive.ulDriveSpeed = 5;

	printf("Enter PowerZoomDrive 0 - OFF, 1- ON\n");
	scanf("%d", &stPowerZoomDrive.ulPowerZoomDrive);
	printf("Enter DriveDirection 1 - W, 2 - T\n");
	scanf("%d", &stPowerZoomDrive.ulDriveDirection);
	printf("Enter DriveSpeed 0 ~ 10\n");
	scanf("%d", &stPowerZoomDrive.ulDriveSpeed);
	printf("\n");

	NKERROR lerror = g_pMAIDSetCapability(kNkMAIDCapability_PowerZoomDrive, &stPowerZoomDrive, kNkMAIDDataType_GenericPtr);
	PERROR(lerror);

	return TRUE;
}

BOOL GetSetSpecialShootingSettingInfo()
{
	bool set_cap_applicable = false;
	NKMAIDCaptureInfoDataset stCaptureInfoDataSet;
	memset(&stCaptureInfoDataSet, 0, sizeof(NKMAIDCaptureInfoDataset));

	ULONG ulShootingType;
	printf("Select Shooting Mode. Interval: 1, FocusShift: 2\n");
	scanf("%d", &ulShootingType);

	if (ulShootingType == kNKMAIDSpecialShootingMode_FocusShift)
		stCaptureInfoDataSet.usShootingType = kNKMAIDSpecialShootingMode_FocusShift;
	else if (ulShootingType == kNKMAIDSpecialShootingMode_Interval)
		stCaptureInfoDataSet.usShootingType = kNKMAIDSpecialShootingMode_Interval;
	else
	{
		printf("Invalid Shooting Mode.");
		return FALSE;
	}

	LPVOID pCapValue = &stCaptureInfoDataSet;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_SpecialShootingSettingInfo, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_SpecialShootingSettingInfo, ulDataType) == false)
		return FALSE;
	if (ulDataType != kNkMAIDCapType_Generic) return FALSE;

	NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_SpecialShootingSettingInfo, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		printf("Failed to get capability value\n");
		return FALSE;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_GenericPtr)
		{
			printf("Invalid data type returned\n");
			return FALSE;
		}
		else
		{
			printf("\n Version: %d\n", (ULONG)stCaptureInfoDataSet.usVersion);
			printf("\n ShootingType: %d\n", (ULONG)stCaptureInfoDataSet.usShootingType);
			printf("\n NumShorts: %d\n", stCaptureInfoDataSet.ulNumShorts);
			printf("\n ShootingTime: %d\n", stCaptureInfoDataSet.ulShootingTime);
		}
	}

	return TRUE;
}

BOOL GetSetStorageIDS(LPNkMAIDStorageIDSList pStorageIds)
{
	if (pStorageIds == NULL) return FALSE;

	LPVOID pCapValue = pStorageIds;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_GetStorageIDS, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_GetStorageIDS, ulDataType) == false)
		return FALSE;
	if (ulDataType != kNkMAIDCapType_Generic) return FALSE;

	NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_GetStorageIDS, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		printf("Failed to get capability value\n");
		return FALSE;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_GenericPtr)
		{
			printf("Invalid data type returned\n");
			return FALSE;
		}
		else
		{
			printf("\n ulArrayCount: %d\n", pStorageIds->ulArrayCount);
		}
	}

	return TRUE;
}

BOOL GetSetStorageInfoDataSet()
{
	NkMAIDStorageIDSList stStorageIDSList;
	if (GetSetStorageIDS(&stStorageIDSList) == FALSE)
		return FALSE;

	if (stStorageIDSList.ulArrayCount == 0)
		return FALSE;

	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_GetStorageInfoDataSet, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_GetStorageInfoDataSet, ulDataType) == false)
		return FALSE;

	if (ulDataType != kNkMAIDCapType_Generic) return FALSE;

	NkMAIDStorageInfoDataSet stStorageInfoDataSet[64];

	for (ULONG i = 0; i < stStorageIDSList.ulArrayCount; i++)
	{
		stStorageInfoDataSet[i].ulStorageId = stStorageIDSList.ulStorageIdArrays[i];
		LPVOID pCapValue = &stStorageInfoDataSet[i];
		NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_GetStorageInfoDataSet, kNkSDKGetSettingValue, pCapValue, eDataType);

		if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
		{
			printf("Failed to get capability value\n");
			return FALSE;
		}
		else
		{
			if (eDataType != kNkMAIDDataType_GenericPtr)
			{
				printf("Invalid data type returned\n");
				return FALSE;
			}
		}
	}

	return TRUE;
}

BOOL InitialRegistrationPictureControlData()
{
	bool set_cap_applicable = false;
	NkMAIDPicCtrlData nPicCtrlData;
	memset(&nPicCtrlData, 0, sizeof(NkMAIDPicCtrlData));
	nPicCtrlData.ulPicCtrlItem = kNkMAIDMoviePictureControl_Custom1;
	nPicCtrlData.bModifiedFlag = true;
	nPicCtrlData.ulSize = 614;
	char buff[614];
	nPicCtrlData.pData = (void*)&buff[0];
	LPVOID pCapValue = &nPicCtrlData;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_PictureControlDataEx2, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_PictureControlDataEx2, ulDataType) == false)
		return FALSE;

	if (ulDataType != kNkMAIDCapType_Generic)
		return FALSE;

	NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_PictureControlDataEx2, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		printf("Failed to get capability value\n");
		return FALSE;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_GenericPtr)
		{
			printf("Invalid data type returned\n");
			return FALSE;
		}
	}

	if (CheckCapability(kNkMAIDCapability_PictureControlDataEx2, kNkMAIDCapOperation_Set) == false)
		return FALSE;

	lerror = g_pMAIDSetCapability(kNkMAIDCapability_PictureControlDataEx2, &nPicCtrlData, kNkMAIDDataType_GenericPtr);
	PERROR(lerror);

	return TRUE;
}

BOOL GetPictureControlData()
{
	bool set_cap_applicable = false;
	NkMAIDPicCtrlData nPicCtrlData;
	memset(&nPicCtrlData, 0, sizeof(NkMAIDPicCtrlData));
	nPicCtrlData.ulPicCtrlItem = kNkMAIDMoviePictureControl_Custom1;
	nPicCtrlData.bModifiedFlag = false;
	nPicCtrlData.ulSize = 614;
	char buff[614];
	nPicCtrlData.pData = (void*)&buff[0];
	LPVOID pCapValue = &nPicCtrlData;
	eNkMAIDDataType eDataType = kNkMAIDDataType_GenericPtr;

	if (CheckCapability(kNkMAIDCapability_PictureControlDataEx2, kNkMAIDCapOperation_Get) == false)
		return FALSE;

	// check data type of the capability
	ULONG ulDataType;
	if (GetCapabilityType(kNkMAIDCapability_PictureControlDataEx2, ulDataType) == false)
		return FALSE;

	if (ulDataType != kNkMAIDCapType_Generic)
		return FALSE;

	NKERROR lerror = g_pMAIDGetCapability(kNkMAIDCapability_PictureControlDataEx2, kNkSDKGetSettingValue, pCapValue, eDataType);

	if (lerror != kNkMAIDResult_NoError || pCapValue == NULL)
	{
		printf("Failed to get capability value\n");
		return FALSE;
	}
	else
	{
		if (eDataType != kNkMAIDDataType_GenericPtr)
		{
			printf("Invalid data type returned\n");
			return FALSE;
		}
		else
		{

			printf("CapValueFound\n");
			char name[21];
			memset(&name[0], 0, 21);
			strncpy(name, buff + 2, 20);
			printf("name = %s", name);
		}
	}

	return TRUE;
}