# 코드 주석 표준

> Developer와 QA 에이전트가 참조하는 코드 주석 규칙입니다.

## 공통 원칙

1. **Why, not What** — 코드가 "무엇을 하는지"가 아닌 "왜 이렇게 하는지"를 설명한다
2. **최신 상태 유지** — 코드 변경 시 관련 주석도 반드시 업데이트한다
3. **자기 설명적 코드 우선** — 주석 대신 명확한 이름과 구조로 의도를 표현한다
4. **TODO/FIXME 형식** — `TODO(담당자): 내용` 또는 `FIXME(담당자): 내용`

## 언어별 규칙

### JavaScript / TypeScript

```typescript
/**
 * 주문 금액에서 쿠폰 할인을 적용한다.
 * 쿠폰 금액이 주문 금액을 초과하면 0원으로 처리한다 (마이너스 방지).
 *
 * @param orderAmount - 주문 금액 (원)
 * @param couponAmount - 쿠폰 할인 금액 (원)
 * @returns 할인 적용된 최종 금액
 */
function applyCoupon(orderAmount: number, couponAmount: number): number {
  // 비즈니스 규칙: 마이너스 결제는 허용하지 않음 (정책 결정 2024-03)
  return Math.max(0, orderAmount - couponAmount);
}
```

### Python

```python
def apply_coupon(order_amount: int, coupon_amount: int) -> int:
    """주문 금액에서 쿠폰 할인을 적용한다.

    쿠폰 금액이 주문 금액을 초과하면 0원으로 처리한다 (마이너스 방지).

    Args:
        order_amount: 주문 금액 (원)
        coupon_amount: 쿠폰 할인 금액 (원)

    Returns:
        할인 적용된 최종 금액
    """
    # 비즈니스 규칙: 마이너스 결제 불가 (정책 결정 2024-03)
    return max(0, order_amount - coupon_amount)
```

### Java

```java
/**
 * 주문 금액에서 쿠폰 할인을 적용한다.
 * 쿠폰 금액이 주문 금액을 초과하면 0원으로 처리한다 (마이너스 방지).
 *
 * @param orderAmount 주문 금액 (원)
 * @param couponAmount 쿠폰 할인 금액 (원)
 * @return 할인 적용된 최종 금액
 */
public int applyCoupon(int orderAmount, int couponAmount) {
    // 비즈니스 규칙: 마이너스 결제 불가 (정책 결정 2024-03)
    return Math.max(0, orderAmount - couponAmount);
}
```

## 금지 사항

- 코드 그대로 반복하는 주석: `// i를 1 증가시킨다`
- 주석 처리된 코드 (삭제하거나 git에 맡길 것)
- 비속어, 감정적 표현
- 저작권/라이선스 없이 복사한 코드
