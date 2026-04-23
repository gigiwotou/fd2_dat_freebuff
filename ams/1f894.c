void __usercall sub_1F894(
        int a1@<edx>,
        int n99_1@<ebx>,
        int n100_1@<ebp>,
        int n15_2@<esi>,
        __int32 a5@<eax>,
        int a6@<ecx>)
{
  int n3_1; // ebp
  int v8; // eax
  __int32 v9; // eax
  int v10; // eax
  int v11; // eax
  __int32 v12; // eax
  int n15_1; // edi
  int n5; // esi
  __int64 v15; // rax
  int n535; // esi
  int v17; // eax
  int v18; // ebx
  int n40; // esi
  int _FDOTHER.DAT__2; // ebx
  int n40_1; // esi
  int n3; // ebx
  int v23; // esi
  int n4; // esi
  int n4_1; // [esp-Ch] [ebp-78h]
  int n15_3; // [esp-8h] [ebp-74h]
  int n99_2; // [esp-4h] [ebp-70h]
  _DWORD dst_[17]; // [esp+0h] [ebp-6Ch] BYREF
  __int16 *_FDOTHER.DAT__1; // [esp+44h] [ebp-28h]
  int v30; // [esp+48h] [ebp-24h]
  int n12; // [esp+4Ch] [ebp-20h]
  int v32; // [esp+50h] [ebp-1Ch]
  int _FDOTHER.DAT_; // [esp+54h] [ebp-18h]
  int n11_1; // [esp+58h] [ebp-14h]
  int n100; // [esp+5Ch] [ebp-10h]
  int v36; // [esp+60h] [ebp-Ch]
  int n15; // [esp+64h] [ebp-8h]
  int n99; // [esp+68h] [ebp-4h]

  sub_3702F(a5, a1, n99_1, a6, 136); /*0x1f899*/
  n99 = n99_1; /*0x1f89e*/
  n15 = n15_2; /*0x1f89f*/
  n100 = n100_1; /*0x1f8a1*/
  v32 = 1; /*0x1f8a5*/
  dst_[16] = 0; /*0x1f8ad*/
  n3_1 = 0; /*0x1f8b5*/
  v30 = 0; /*0x1f8b7*/
  n12 = 12; /*0x1f8bb*/
  LOBYTE(n11_1) = 0; /*0x1f8c3*/
  qmemcpy(dst_, &src, 0x3Cu); /*0x1f8d4*/
  _FDOTHER.DAT_ = sub_111BA((int)aFdotherDat, 0, 77);// "FDOTHER.DAT" /*0x1f8e6*/
  memset(655360, 0, 64000); /*0x1f8f5*/
  FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 76);// "FDOTHER.DAT" /*0x1f912*/
  sub_11D40(0, 255, 64); /*0x1f91f*/
  _FDOTHER.DAT__1 = (__int16 *)sub_111BA((int)aFdotherDat, 0, 74);// "FDOTHER.DAT" /*0x1f937*/
  LOBYTE(v8) = sub_4E98D(_FDOTHER.DAT__1, 0, 0, 655360, 320, -1); /*0x1f94a*/
  v9 = sub_1F525(v8); /*0x1f952*/
  v10 = sub_17AA9(v9, a1, n99_1, 0, 1); /*0x1f959*/
  v11 = sub_17AA9(v10, a1, n99_1, 0, 30); /*0x1f963*/
  sub_1F882(v11, a1, n99_1, 0); /*0x1f96b*/
  FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 99);// "FDOTHER.DAT" /*0x1f985*/
  memset(655360, 0, 64000); /*0x1f995*/
  sub_11D40(0, 255, 0); /*0x1f9a4*/
  sub_20421(3, 90, 1); /*0x1f9b2*/
  sub_1F882(v12, a1, n99_1, 0); /*0x1f9ba*/
  memset(655360, 0, 64000); /*0x1f9ca*/
  FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 101);// "FDOTHER.DAT" /*0x1f9e7*/
  sub_11D40(0, 255, 64); /*0x1f9f4*/
  n15_1 = malloc(&loc_396C0); /*0x1fa09*/
  memset(n15_1, 0, &loc_396C0); /*0x1fa12*/
  for ( n5 = 0; n5 < 5; ++n5 ) /*0x1fa1a*/
  {
    _FDOTHER.DAT__1 = (__int16 *)sub_111BA((int)aFdotherDat, (int)_FDOTHER.DAT__1, n5 + 69);// "FDOTHER.DAT" /*0x1fa33*/
    sub_4E98D(_FDOTHER.DAT__1, 0, 147 * n5, n15_1, 320, -1); /*0x1fa49*/
  }
  sub_4E381(); /*0x1fa57*/
  if ( dword_53A45 ) /*0x1fa63*/
    free(dword_53A45); /*0x1fa6b*/
  v15 = malloc(160); /*0x1fa78*/
  dword_53A45 = v15; /*0x1fa80*/
  for ( n535 = 535; ; --n535 ) /*0x1fa85*/
  {
    if ( n535 < 0 ) /*0x1fa8f*/
    {
LABEL_32:
      for ( n40 = 40; n40 >= 0; --n40 ) /*0x1fc66*/
      {
        sub_2DF01(0, 255, n40, 63, 0, 0); /*0x1fc7b*/
        j___delay(8); /*0x1fc85*/
      }
      j___delay(100); /*0x1fc94*/
      sub_4E381(); /*0x1fc9c*/
      free(n15_1); /*0x1fca2*/
      free(v32); /*0x1fcae*/
      _FDOTHER.DAT__2 = sub_111BA((int)aFdotherDat, _FDOTHER.DAT_, 7);// "FDOTHER.DAT" /*0x1fcc6*/
      _FDOTHER.DAT_ = _FDOTHER.DAT__2;          // "FDOTHER.DAT" /*0x1fccb*/
      FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 8);// "FDOTHER.DAT" /*0x1fce4*/
      memset(655360, 0, 64000); /*0x1fcf5*/
      sub_11D40(0, 255, 0); /*0x1fd06*/
      sub_20421(1, 15, 1); /*0x1fd14*/
      sub_25B45(v36, 3, 1); /*0x1fd24*/
      sub_11DF2(0, 255, 64); /*0x1fd35*/
      sub_16886(655360, 320, _FDOTHER.DAT__2, 0); /*0x1fd4a*/
      for ( n40_1 = 0; n40_1 <= 40; ++n40_1 ) /*0x1fd52*/
      {
        sub_2DF01(0, 255, n40_1, 56, 60, 63); /*0x1fd64*/
        j___delay(8); /*0x1fd6e*/
      }
      sub_4E381(); /*0x1fd7c*/
      n3 = fopen((int)aFd2Sav_3, (int)aRb_3);   // "rb" /*0x1fd90*/
      if ( n3 ) /*0x1fd97*/
      {
        v15 = malloc(22987); /*0x1fda2*/
        v23 = v15; /*0x1fda7*/
        v30 = v15; /*0x1fdac*/
        sub_373CA((_BYTE *)v15, 1u, 22987, n3); /*0x1fdb9*/
        fclose(n3); /*0x1fdc2*/
        sub_4DF28((char *)v23, 22987); /*0x1fdd0*/
        if ( sub_4DF09((_BYTE *)v23, 22987) == *(_DWORD *)(v23 + 22983) ) /*0x1fdf2*/
        {
          n100 = 2; /*0x1fdf4*/
          if ( *(unsigned __int8 *)(v23 + 12485) != 255 ) /*0x1fe05*/
            n100 = 3; /*0x1fe07*/
        }
        free(v30); /*0x1fe13*/
      }
      LODWORD(v15) = sub_1FF79(_FDOTHER.DAT_, 0, n100); /*0x1fe24*/
      while ( !n12 ) /*0x1fe31*/
      {
        sub_1FF79(_FDOTHER.DAT_, n3_1, n100); /*0x1fe40*/
        HIBYTE(::n3) = 16; /*0x1fe48*/
        int386(22, &::n3, &::n3); /*0x1fe5b*/
        LODWORD(v15) = HIBYTE(::n3); /*0x1fe63*/
        n3 = n100 - 1; /*0x1fe6e*/
        if ( HIBYTE(::n3) == 72 ) /*0x1fe72*/
        {
          LODWORD(v15) = sub_25A96(v36, 2, 1); /*0x1fe7c*/
          if ( n3_1 ) /*0x1fe86*/
            --n3_1; /*0x1fe8c*/
          else
            n3_1 = n3; /*0x1fe88*/
        }
        else if ( HIBYTE(::n3) == 80 ) /*0x1fe92*/
        {
          LODWORD(v15) = sub_25A96(v36, 2, 1); /*0x1fe9c*/
          if ( n3_1 == n3 ) /*0x1fea6*/
            n3_1 ^= n3; /*0x1fea8*/
          else
            ++n3_1; /*0x1feac*/
        }
        else
        {
          n3 = (unsigned __int8)::n3; /*0x1feb2*/
          if ( (unsigned __int8)::n3 == 13 || (unsigned __int8)::n3 == 32 || HIBYTE(::n3) == 224 || HIBYTE(::n3) == 82 ) /*0x1fecd*/
          {
            LODWORD(v15) = sub_25A96(v36, 1, 1); /*0x1fedb*/
            n12 = 1; /*0x1fee3*/
          }
        }
      }
      for ( n4 = 0; n4 < 4; ++n4 ) /*0x1fef0*/
      {
        sub_1FF79(_FDOTHER.DAT_, -1, n100); /*0x1fefe*/
        j___delay(80); /*0x1ff08*/
        sub_1FF79(_FDOTHER.DAT_, n3_1, n100); /*0x1ff19*/
        LODWORD(v15) = j___delay(80); /*0x1ff23*/
      }
      sub_1F882(v15, SHIDWORD(v15), n3, 0); /*0x1ff31*/
      memset(655360, 0, 64000); /*0x1ff42*/
      free(_FDOTHER.DAT_); /*0x1ff4e*/
      sub_25A96(v36, -1, 1); /*0x1ff5e*/
      free(v36); /*0x1ff6a*/
      JUMPOUT(0x13994); /*0x13994*/
    }
    v17 = sub_11EB0(655360, 320, n15_1 + 320 * n535, 320, 320, 200); /*0x1fabb*/
    if ( n535 == 535 ) /*0x1fac9*/
      sub_1F525(v17); /*0x1facb*/
    LODWORD(v15) = 320 * n535; /*0x1fad7*/
    v18 = n15_1 + 320 * n535; /*0x1fada*/
    if ( n535 == 25 ) /*0x1fae0*/
      break; /*0x1fae0*/
    switch ( n535 ) /*0x1fb3c*/
    {
      case 330: /*0x1fb3c*/
        LODWORD(v15) = sub_1F882(v15, SHIDWORD(v15), v18, 0); /*0x1fb3e*/
        LODWORD(v15) = sub_1F81E(v15, SHIDWORD(v15), v18, 0, 4, 90, 99); /*0x1fb49*/
        dst_[2] = 0; /*0x1fb51*/
        dst_[1] = 50; /*0x1fb53*/
        dst_[0] = 5; /*0x1fb55*/
        goto LABEL_13; /*0x1fb57*/
      case 210: /*0x1fb3c*/
        LODWORD(v15) = sub_1F882(v15, SHIDWORD(v15), v18, 0); /*0x1fb61*/
        LODWORD(v15) = sub_1F81E(v15, SHIDWORD(v15), v18, 0, 6, 90, 99); /*0x1fb6c*/
        dst_[2] = 0; /*0x1fb74*/
        dst_[1] = 50; /*0x1fb76*/
        dst_[0] = 7; /*0x1fb78*/
        goto LABEL_13; /*0x1fb7a*/
      case 110: /*0x1fb3c*/
        LODWORD(v15) = sub_1F882(v15, SHIDWORD(v15), v18, 0); /*0x1fb84*/
        sub_1F81E(v15, SHIDWORD(v15), v18, 0, 8, 90, 99); /*0x1fb8f*/
        goto LABEL_14; /*0x1fb8f*/
      case 450: /*0x1fb3c*/
        sub_1F73F(100, 99, n15_1, 450); /*0x1fba2*/
        break;
      case 10: /*0x1fb3c*/
        sub_1F73F(75, 76, n15_1, 10); /*0x1fbaf*/
        break;
    }
LABEL_25:
    if ( n535 == dst_[(unsigned __int8)n15 + 3] ) /*0x1fbbf*/
    {
      n11_1 = 0; /*0x1fbc1*/
      sub_25A96(v36, 0, 1); /*0x1fbd1*/
      FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 102);// "FDOTHER.DAT" /*0x1fbee*/
      sub_11D40(0, 255, 0); /*0x1fbfc*/
      LOBYTE(n15) = n15 + 1; /*0x1fc04*/
    }
    if ( n11_1 == 11 ) /*0x1fc0d*/
    {
      FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 101);// "FDOTHER.DAT" /*0x1fc24*/
      sub_11D40(0, 255, 0); /*0x1fc32*/
    }
    ++n11_1; /*0x1fc3c*/
    j___delay(30); /*0x1fc40*/
    if ( !n535 ) /*0x1fc4a*/
      j___delay(1000); /*0x1fc51*/
    if ( sub_10620() ) /*0x1fc59*/
      goto LABEL_32; /*0x1fc60*/
  }
  n99_2 = 0; /*0x1fae2*/
  n15_3 = 15; /*0x1fae4*/
  n4_1 = 0; /*0x1fae6*/
LABEL_13:
  sub_1F81E(v15, SHIDWORD(v15), v18, 0, n4_1, n15_3, n99_2); /*0x1fae8*/
LABEL_14:
  sub_11EB0(655360, 320, n15_1 + 320 * n535, 320, 320, 200); /*0x1faed*/
  FDOTHER_DAT = sub_111BA((int)aFdotherDat, FDOTHER_DAT, 101);// "FDOTHER.DAT" /*0x1fb27*/
  sub_1F525(FDOTHER_DAT); /*0x1fb2c*/
  goto LABEL_25; /*0x1fb31*/
}
/* Orphan comments:
"rb"
*/