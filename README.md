# CrossWeave

384비트 공개 순열과 AEAD 하나를 연구하는 C11 프로젝트다.
공식 구현·명세는 현재 설계 하나만 유지한다. P12/P16은 라운드 수가 다른
내부 호출이며 별도 알고리즘 버전이 아니다.

**연구용이며 독립 보안 검토를 받지 않았다. 실제 비밀 보호에 사용하면 안 된다.**

- [현재 명세](docs/spec_ko.md)
- [보안 모델과 연구 근거](docs/security_ko.md)
- [진행 상태와 재현 명령](docs/progress_ko.md)

현재 작업 범위는 순열·역순열 구현과 초기 구조 공격 검사까지다.
AEAD C 구현은 다음 범위이며 아직 제공하지 않는다. 제3자 코드를 가져오지
않으며 배포 라이선스는 아직 지정하지 않았다.

## 빌드와 검증

필요 도구는 C11 컴파일러, make, ar, Python 3.12 이상이다. Python 패키지나
런타임 암호 라이브러리는 필요하지 않다.

```sh
make
make check
make research
make sanitize
```

정적 라이브러리는 `build/libcrossweave.a`다. 공개 API는
`include/crossweave.h`에 있으며 48바이트 LE 상태를 제자리 갱신한다.
`make check`는 고정 중간 벡터·P12/P16·역순열·153개 라운드 구간·오류와
출력 보존·별도 수식 oracle·SHAKE 부품·프레이밍을 검사한다.
`make research`는 [기록된 초기 공격 실험](docs/security_ko.md)을 재현한다.
관측이 달라지거나 소스·명세·KAT 지문이 바뀌면 재분석을 요구한다.

한 라운드 구별자는 확인했으며 전체 라운드 안전성은 미확정이다. SHAKE는
공개 상수 생성 시에만 사용하는 부품이다. 벡터 재생성은 명세·코어 변경을
검토한 다음에만 실행한다.

```sh
python3 tests/constants.py --write
python3 tests/vectors.py --write
make check
python3 research/early_gate.py build/oracle_driver --write docs/early_gate.json
make research
```

이 절차에서 공격 결과가 달라지면 원인을 조사해야 한다. 기준 결과를 단순히
덮어써 통과시키면 안 된다. 로컬 실행 환경의 LeakSanitizer 제약은 진행 기록에
구분해 기록했다. 원격 CI는 GCC/Clang과 ASan/UBSan을 실행하도록 구성했다.
